FROM ninai/pipeline:base
LABEL maintainer="Edgar Y. Walker, Fabian Sinz, Erick Cobos, Donnie Kim"

WORKDIR /data

# Install pipeline
COPY . /data/pipeline
RUN pip3 install -e pipeline/python/
RUN apt-get install -y graphviz
RUN apt-get install -y graphviz-dev
ENTRYPOINT ["/bin/bash"]
