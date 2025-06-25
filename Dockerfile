FROM ghcr.io/eolab-hsrw/easy-px4:ubuntu-22.04

RUN apt-get update && rm -rf /var/lib/apt/lists/*

COPY . /eolab-drones
WORKDIR /eolab-drones

RUN pip3 install .
