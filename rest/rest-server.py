##
import jsonpickle
import json
import os
from io import BytesIO
import base64
import redis
import hashlib
from minio import Minio
from minio.error import InvalidResponseError
from progress import Progress
from flask import Flask, request, Response, send_file

##
## Configure test vs. production
##
redisHost = os.getenv('REDIS_HOST') or '172.17.0.1'
minioHost = os.getenv('MINIO_HOST') or '172.17.0.1:9000'
minioUser = os.getenv('MINIO_USER') or 'ROOTUSER'
minioPasswd = os.getenv('MINIO_PASSWD') or 'CHANGEME123'

minioClient = Minio(minioHost,
               secure=False,
               access_key=minioUser,
               secret_key=minioPasswd)

queueBucketName='queue'
outPutBucketName='output'

if not minioClient.bucket_exists(queueBucketName):
    minioClient.make_bucket(queueBucketName)
    print('Created Bucket queue')

if not minioClient.bucket_exists(outPutBucketName):
    minioClient.make_bucket(outPutBucketName)
    print('Created Bucket output')

print('Connecting to redis({}) and minio({})'.format(redisHost, minioHost))

app = Flask(__name__)
# Four Redis databases as described
redisNameToHash = redis.Redis(host=redisHost, db=1)    # Key -> Value
redisHashToName = redis.Redis(host=redisHost, db=2)    # Key -> Set
redisQueue = redis.Redis(host=redisHost, db=3) #queue list

# Added this for health checking
@app.route('/', methods=['GET'])
def hello():
    return 'Added this, for health checking'
# When the Music filename is provided for separation
@app.route('/separate/<path:fileName>', methods=['POST'])
def separate_music(fileName):
    print(fileName)
    try:
        # Get the hash of the filename
        hashedMessage = hashlib.md5(fileName.encode()).hexdigest()
        # If an music is being scanned for the first time
        if redisNameToHash.get(fileName)==None:
            content = request.get_json()
            music_data = content['music_data']
            
            # Add mp3 file to minio bucket
            minioClient.put_object(queueBucketName, fileName, BytesIO(base64.b64decode(music_data)), length=len(base64.b64decode(music_data)), part_size=10*1024*1024, content_type='audio/mpeg', progress=Progress())

            # Add the hashed name to 2 redis databases as required
            redisNameToHash.set(fileName, hashedMessage)
            redisHashToName.sadd(hashedMessage,fileName)
            # Add to queue
            message = {
                'fileName': fileName
            }
            redisQueue.lpush('toWorker', json.dumps(message))
            print('\n Sent %r' % hashedMessage)

            # Send back the response in the required format
            response = {
                'hash': hashedMessage, 
                'reason': 'Song enqueued for separation'
            }
            response_pickled = jsonpickle.encode(response)
            return Response(response=response_pickled, status=200, mimetype='application/json')
        # If a music hash has already been added, just provide the hash
        else:
            response = {
                'hash': hashedMessage, 
                'reason': 'Song already separated. Use hash to retrieve the audios.'
            }
            response_pickled = jsonpickle.encode(response)
            redisHashToName.sadd(hashedMessage,fileName)
            return Response(response=response_pickled, status=200, mimetype='application/json')
    except Exception as e:
        print(e)

@app.route('/queue', methods=['GET'])
def get_from_queue():
    length = redisQueue.llen('toWorker')
    queue = []
    for x in range(0,length):
        print(redisQueue.lindex('toWorker',x).decode())
        queue.append(redisQueue.lindex('toWorker',x).decode())

    response={
        'queue': queue
    }

    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled, status=200, mimetype='application/json')

@app.route('/track/<path:hashVal>/<path:audio>', methods=['GET'])
def download_tack_file(hashVal, audio):
    # send requested audio track to client
    audio_data = ''
    filePath = hashVal+'/'+audio+'.mp3'
    available_objects = list(map(
        lambda x: x.object_name,
        minioClient.list_objects(outPutBucketName, hashVal, recursive=True)
    ))

    if(len(available_objects) > 0 and filePath in available_objects):
        try:
            response = minioClient.get_object(outPutBucketName, filePath)
            audio_data = BytesIO(response.data)
        except Exception as e:
            print(e)
        finally:
            response.close()
            response.release_conn()
        return send_file(audio_data, mimetype='audio/mpeg',  download_name='./audio'+'.mp3', as_attachment=True)
    else:
        response={
            'status': 'Failed',
            'reason': 'File do not exist'
        }
        response_pickled = jsonpickle.encode(response)
        return Response(response=response_pickled, status=200, mimetype='application/json')


@app.route('/delete/<path:hashVal>', methods=['Delete'])
def deleteFromRedisAndMinIO(hashVal):
    response = {
        'delete': True, 
        'reason': 'Hash Found'
    }

    # get members of hashVal set
    fileNames = redisHashToName.smembers(hashVal)
    if len(fileNames) == 0:
        response['delete'] = False
        response['reason'] = 'Hash Not Found'
    else:
        # remove track from redis redis i.e. from both redisHashToName and redisNameToHash
        fileNamesToRemove = []
        for fileName in fileNames:
            fileNamesToRemove.append(fileName.decode())
        #remove all values inside hashVal set in redisHashToName
        redisHashToName.srem(hashVal, ','.join(fileNamesToRemove))
        #remove all keys from redisNameToHash
        redisNameToHash.delete(','.join(fileNamesToRemove))

        # remove track from minio
        try:
            delete_objects = map(
                lambda x: x.object_name,
                minioClient.list_objects(outPutBucketName, hashVal, recursive=True)
            )
            for file in delete_objects:
                minioClient.remove_object(outPutBucketName, file)
        except InvalidResponseError as e:
            print(e)

    response_pickled = jsonpickle.encode(response)
    return Response(response=response_pickled, status=200, mimetype='application/json')

app.run(host='0.0.0.0', port=8080)