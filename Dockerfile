# Start from weaveworks/scope, so that we have a docker client built in.
FROM ubuntu:xenial
LABEL works.weave.role=system

RUN apt-get update && apt-get upgrade
RUN apt install -y python3-pip
RUN pip install docker-py

# Add our plugin
ADD ./volume-count.py /usr/bin/
ENTRYPOINT ["/usr/bin/volume-count.py"]
