# EOLab's Drones Firmwares

![Build Firmwares](https://github.com/EOLab-HSRW/drones-fw/actions/workflows/build.yml/badge.svg)

## Build Firmware Locally

```console
bash build.sh <DRONE_NAME>
```

for example to build the firmware of `platypus`:

```console
bash build.sh platypus
```

## The Little Spec

Specting a directory with the following files (name sensitive)
- `info.toml`
- `params.airframe`
- `board.modules`
- `sitl.modules`
