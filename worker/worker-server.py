#
# Worker server
#
import os
import sys
import redis
from minio import Minio
import json
from progress import Progress

##
## Configure test vs. production
##
redisHost = os.getenv("REDIS_HOST") or "172.17.0.1"
minioHost = os.getenv("MINIO_HOST") or "172.17.0.1:9000"
minioUser = os.getenv("MINIO_USER") or "ROOTUSER"
minioPasswd = os.getenv("MINIO_PASSWD") or "CHANGEME123"

minioClient = Minio(minioHost,
               secure=False,
               access_key=minioUser,
               secret_key=minioPasswd)

queueBucketName='queue'
outputBucketName='output'

buckets = minioClient.list_buckets()
for bucket in buckets:
    print(bucket.name, bucket.creation_date)

print("Connecting to redis({})".format(redisHost))

# Four Redis databases as described
redisNameToHash = redis.Redis(host=redisHost, db=1)    # Key -> Value
redisHashToName = redis.Redis(host=redisHost, db=2)    # Key -> Set
redisQueue = redis.Redis(host=redisHost, db=3) #queue list

print("Hello. I am up and running. Thanks!")


while True:
    try:
        message=redisQueue.brpop('toWorker', timeout=None)
        
        actual_message=json.loads(message[1])
        fileName=actual_message['fileName']
        print(fileName)
        
        minioClient.fget_object(queueBucketName, fileName, '/data/input/'+fileName)
        print('Downloaded file: '+fileName+' from queue')

        minioClient.remove_object(queueBucketName, fileName)
        print('Deleted file: '+fileName+' from queue')

        os.system('python3 -m demucs --mp3 --out /data/output /data/input/'+fileName)
        
        print('Done with audio split')
        print('Starting file uploads to output bucket in minio')

        namehash = (redisNameToHash.get(fileName)).decode()

        print('File: '+fileName+' hash: '+ namehash)

        if not minioClient.bucket_exists(outputBucketName):
            minioClient.make_bucket(outputBucketName)

        fileName = fileName.split('.')[0] # need this because demucs stores output in fileName and not fileName.mp3
        outPutDir = '../data/output/mdx_extra_q/'+fileName+'/'

        dir_contents = os.listdir(outPutDir)
        
        for file in dir_contents:
            print('\nUploading file: '+ file)
            try:
                minioClient.fput_object(outputBucketName, namehash+'/'+file, outPutDir+file, content_type="audio/mpeg", progress=Progress())
            except Exception as e:
                print(e)
        
        print('\nFinished all file uploads')
        print('Waiting for next message from redis')
    except Exception as error:
        print(error)

