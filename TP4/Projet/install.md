# Pour le projet 

sudo apt update

sudo apt install -y \
  build-essential \
  python3 python3-dev python3-pip \
  scons \
  git \
  libprotobuf-dev protobuf-compiler \
  libboost-all-dev \
  zlib1g-dev \
  libsqlite3-dev

pip3 install --user pyparsing

scons build/ARM/gem5.opt -j$(nproc)

# pour cacti 

sudo apt install -y g++-multilib libc6-dev-i386

# Pour la compilation ARM

Téléchargez :

  wget https://musl.cc/arm-linux-musleabihf-cross.tgz

  