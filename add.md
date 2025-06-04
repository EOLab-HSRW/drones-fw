# How to Add a New Drone

1. Define the name of the drone with **a single word** using **ONLY alphanumeric** and **lowercase**. E.g. `platypus`, `sar` or `newbie`.

2. Create a new directory with the name of the drone under [catalog/drones](./catalog/drones/)

3. Initialize the following files with in the folder

```
newbie/
├─ info.toml
├─ params.airframe
├─ board.modules
├─ sitl.modules
```

Add all the relevant metadata in the file `info.toml`. E.g. for `newbie`

```toml
name = "protoflyer"
id = 22999
vendor = "px4"
model = "fmu-v3"
px4_version = "v1.15.4"
custom_fw_version = "3.5.7"
components = ["radiomaster_tx16s"]
```

4. In `board.modules` and `sitl.modules` specify the [modules](https://docs.px4.io/main/en/modules/modules_main.html) to enable and/or disable. For complete examples see the file [multicopter.px4board](https://github.com/PX4/PX4-Autopilot/blob/main/boards/px4/fmu-v6x/multicopter.px4board) in the official [`PX4-Autopilot`](https://github.com/PX4/PX4-Autopilot) repo as a reference use case.

5. In `params.airframe` set your parameters. E.g.:

```sh 22100_eolab_newbie
#!/bin/sh
#
# @name EOLab Newbie
#
# @type Hexarotor x
# @class Copter
#
# @maintainer Harley Lara <contact@harleylara.com>
#

. ${R}etc/init.d/rc.mc_defaults
. ${R}etc/init.d/radiomaster_tx16s # <- this is using the module defined in `components`

param set-default MAV_0_CONFIG 101
param set-default MAV_1_CONFIG 0

param set-default RC_CRSF_PRT_CFG 102

# add the rest of the firmware parameters here
```

Done.
