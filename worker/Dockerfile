FROM xserrat/facebook-demucs:latest

RUN apt-get update
RUN apt-get install -y python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install --upgrade requests
RUN pip3 install redis
RUN pip3 install minio

RUN mkdir /worker
RUN chmod -R 777 /worker
WORKDIR /worker
COPY . /worker

CMD ["python3 -u worker-server.py"]