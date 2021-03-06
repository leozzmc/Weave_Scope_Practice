# Start from weaveworks/scope, so that we have a docker client built in.
FROM ubuntu:xenial
LABEL works.weave.role=system


RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update && apt-get upgrade
# For executing "from docker import APIClient" 
RUN apt install -y python3.5 

RUN apt install -y python3-pip
RUN pip3 install docker-py

# Add our plugin
ADD ./volume-count.py /usr/bin/
ENTRYPOINT ["/usr/bin/volume-count.py"]
