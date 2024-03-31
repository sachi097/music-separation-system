# Music Separation System
![separation](images/music_separation.png)

Music-Separation-as-a-service (MSaaS)
## Overview
Created a kubernetes cluster that provides a REST API for automatic music separation service and prepares the different tracks for retrieval.

Deployed containers providing the following services.
+ **rest** - The REST frontend will accept API requests for analysis and handle queries concerning MP3's. The REST worker will queue tasks to workers using `redis` queues.
+ **worker** - Worker nodes will receive work requests to analyze MP3's and cache results in a cloud object store (**Min.io**).
+ **redis** - Redis database server for message broker.
### Waveform Source Separation Analysis
The worker will use [open source waveform source separation analysis](https://github.com/facebookresearch/demucs) software from Facebook.

### Setting up Kubernetes
Used Google Cloud's service, GKE.

### Cloud object service

Rather than sending the large MP3 files through Redis, used Min.io object storage system to store the song contents ***and*** the output of the waveform separation. 
Utilized [min.io python interface](https://min.io/docs/minio/linux/developers/python/API.html) to connect to an object storage system like [Min.io](https://min.io/).

One benefit of an object store is that you can control access to those objects & direct the user to download the objects directly from *e.g.* S3 rather than relaying the data through your service.

### Bucket description
- Bucket called "queue" that holds the objects containing MP3 songs to process.
- Bucket called "output" to hold the results ready for download:
![buckets](images/buckets.png)

The "output" bucket has objects named `<songhash>-<track>.mp3` that contain the separate tracks of a song:
![output bucket image](images/output-bucket.png)

### Sample Data
Sample data can be found in data folder.