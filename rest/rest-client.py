#!/usr/bin/env python3
# 
#
# A sample REST client for the music split application
#
import requests
import json
import time
import sys
import base64

def doSeparateMP3(addr, filename, debug=False):
    # prepare headers for http request
    headers = {'content-type': 'application/json'}
    music = open('../data/'+filename, 'rb').read()
    encoded_music = base64.b64encode(music).decode()
    # send http request with music and receive response
    separate_url = addr + '/separate/' + filename
    print(separate_url)
    response = requests.post(separate_url, json={'music_data': encoded_music}, headers=headers)
    if debug:
        # decode response
        print('Response is', response)
        print(json.loads(response.text))

def doGetQueue(addr, debug=False):
    # prepare headers for http request
    headers = {'content-type': 'application/json'}
    # send http request with image and receive response
    queue_url = addr + '/queue'
    response = requests.get(queue_url, headers=headers)
    if debug:
        # decode response
        print('Response is', response)
        print(json.loads(response.text))

def doGetTrack(addr, hashval, track, debug=False):
    url = addr + '/track/' + hashval + '/'+ track
    response = requests.get(url)
    if(response.headers['Content-type'] == 'audio/mpeg'):
        with open('./downloads/'+hashval+'-'+track+'.mp3', 'wb') as binary_file:
            # Write bytes to file
            binary_file.write(response.content)
        print('Response is', response)
        print('Downloaded file')
    else:
        print('Response is', response)
        print(json.loads(response.text))

def doRemoveTrack(addr, hashval, debug=False):
    url = addr + '/delete/' + hashval
    response = requests.delete(url)
    if debug:
        # decode response
        print('Response is', response)
        print(json.loads(response.text))

def doHealthCheck(addr, debug=False):
    url = addr
    response = requests.get(url)
    if debug:
        # decode response
        print('Response is', response)
        print(response.text)

host = sys.argv[1]
cmd = sys.argv[2]

addr = 'http://{}:8080'.format(host)

if cmd == 'separate':
    filename = sys.argv[3]
    start = time.perf_counter()
    doSeparateMP3(addr, filename, True)
    delta = ((time.perf_counter() - start))*1000
    print('Took', delta, 'ms per operation')
elif cmd == 'queue':
    start = time.perf_counter()
    doGetQueue(addr, True)
    delta = ((time.perf_counter() - start))*1000
    print('Took', delta, 'ms per operation')
elif cmd == 'track':
    hashval = sys.argv[3]
    track = sys.argv[4]
    start = time.perf_counter()
    doGetTrack(addr, hashval, track, True)
    delta = ((time.perf_counter() - start))*1000
    print('Took', delta, 'ms per operation')
elif cmd == 'remove':
    hashval = sys.argv[3]
    start = time.perf_counter()
    doRemoveTrack(addr, hashval, True)
    delta = ((time.perf_counter() - start))*1000
    print('Took', delta, 'ms per operation')
elif cmd == 'healthcheck':
    doHealthCheck(addr, True)
else:
    print('Unknown option', cmd)