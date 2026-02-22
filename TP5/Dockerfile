FROM ubuntu:14.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
	nano \
	build-essential \
	git \
	m4 \
	scons \
	zlib1g \
	zlib1g-dev \
	libprotobuf-dev \
	protobuf-compiler \
	libprotoc-dev \
	libgoogle-perftools-dev \
	python3 \
	python3-pip \
	python3-dev \
	python-dev \
	libboost-all-dev \
	pkg-config \
	python3-tk \
	swig \
	gcc-arm-linux-gnueabi \
	g++-arm-linux-gnueabi

WORKDIR /workspace
ENV WORKSPACE=/workspace

RUN git clone https://github.com/gem5/m5threads.git && \
	cd m5threads/tests && \
	make

RUN git clone https://github.com/gem5/gem5.git && \
	cd gem5 && \
	git checkout stable_2014_12_14 && \
	scons build/ARM/gem5.fast -j 12 && \
	cp /workspace/gem5/build/ARM/gem5.fast /usr/local/bin


# Copy files to the container
COPY ./files /workspace

CMD ["/bin/bash"]

