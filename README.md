# EOLab's Drones Firmwares

![Build Firmwares](https://github.com/EOLab-HSRW/drones-fw/actions/workflows/build.yml/badge.svg)

## Build Firmware Locally

```console
eolab_drone build --type [sitl|firmware] --drone [DRONE_NAME]
```

for example to build the firmware of `platypus`:

```console
eolab_drone build --type firmware --drone platypus
```

for building the simulation firmware:

```console
eolab_drone build --type sitl --drone platypus
```
