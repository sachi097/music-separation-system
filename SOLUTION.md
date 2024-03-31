Steps to Run on GKE

1: Create cluster with name demucs-cluster. Below command creats 4 vCPUS and 6GB of RAM for each nodes. Generally, 1 master and 2 workers.
```
gcloud container clusters create demucs-cluster --machine-type=custom-4-6144 --preemptible --release-channel None --zone us-central1-b
```

2: Deploy ingress
```
sudo apt-get install google-cloud-sdk-gke-gcloud-auth-plugin
gcloud container clusters get-credentials demucs-cluster --region us-central1-b
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.0.4/deploy/static/provider/cloud/deploy.yaml
```

3: Deploy Redis
```
cd redis
kubectl create -f redis-deployment.yaml
kubectl create -f redis-service.yaml
cd ..
```

4: Deploy MinIO
```
cd minio
kubectl apply -f minio-deployment.yaml
kubectl create -f minio-ingress.yaml
cd ..
```

5: Login to MinIO UI
```
Option 1:
Go to Services & Ingress in GKE. Click on ingress tab then click the external ip under Frontends column.

Option 2:
echo "MinIO&reg; web URL: http://127.0.0.1:9090/minio" && kubectl port-forward svc/minio 9090

After running above command. Click http://127.0.0.1:9090/minio within cloud shell, this will open new tab for MinIO
UI. Enter username: ROOTUSER password: CHANGEME123 click login (this won't login). To resolve this, go back to cloud
shell press CTRL+C and enter the same command again. Now, go back to MinIO UI click login. You will be inside the 
MinIO UI (Bingo!).
```

6: Deploy Rest-Server - Open up new cloud shell by clicking +
```
cd rest
kubectl create -f rest-deployment.yaml
kubectl create -f rest-service.yaml
cd ..
```

7: Port forward on rest pod to allow rest-client to access it
```
kubectl get pod
copy rest_pod_id
echo "Rest&reg; web URL: http://127.0.0.1:8080/rest" && kubectl port-forward pod/rest_pod_id 8080
```

8: Deploy Demucs Worker - Open up new cloud shell by clicking +
```
cd worker
kubectl create -f worker-deployment.yaml
cd ..
```

9: Look logs of Demuc Worker
```
kubectl get pod
copy woker_pod_id
kubectl logs -f worker_pod_id
```

10: To separate music: Open up new cloud shell by clicking +
```
cd rest
python rest-client.py localhost separate short-dreams.mp3
```

11: To view queue
```
python rest-client.py localhost queue 
```

12: To download track - files will be downloaded at /rest/downloads/
```
python rest-client.py localhost track <hashVal> <type> 
# type = [drums, bass, vocal, other]
```

13: To Delete track
```
python rest-client.py localhost remove <hashVal>
```
