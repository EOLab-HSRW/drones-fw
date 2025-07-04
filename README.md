# EOLab's Drones Firmwares

![Build Firmwares](https://github.com/EOLab-HSRW/drones-fw/actions/workflows/build-firmwares.yml/badge.svg)

## Install

Just for our catalog information:

```
EASY_PX4_INSTALL_DEPS=false EASY_PX4_CLONE_PX4=false pip install git+https://github.com/EOLab-HSRW/drones-fw.git@main#egg=eolab_drones
```

For local development :

```console
pip install .
```

## Build Firmware Locally

```console
eolab_drones build --type [sitl|firmware] --drone [DRONE_NAME]
```

for example to build the firmware of `platypus`:

```console
eolab_drones build --type firmware --drone platypus
```

for building the simulation firmware:

```console
eolab_drones build --type sitl --drone platypus
```
