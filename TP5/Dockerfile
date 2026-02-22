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

# set a GEM5_PATH variable to be able to use the gem5 executable from anywhere

#create alias for gem5
RUN echo "alias gem5='/usr/local/bin/gem5.fast'" >> ~/.bashrc
COPY gem5-stable /workspace/gem5-stable
COPY scripts /workspace/scripts

ENV GEM5_PATH=/workspace/gem5-stable/

# Copy the run scripts to the container



# export 
CMD ["/bin/bash"]