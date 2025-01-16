# How to Add a New Drone

1. Define the name of the drone with **a single word** using **ONLY alphanumeric** and **lowercase**. E.g. `platypus`, `sar` or `newbie`.

2. Add the new drone name to the list `NAME_OPTIONS=("platypus" "sar" "all")` in [`build.sh`](./build.sh).

```sh
NAME_OPTIONS=("platypus" "sar" "newbie" "all")
```

3. Add the case for the new drone name in the function `build_drone()` in [`build.sh`](./build.sh). E.g. for `newbie`

```sh build.sh
build_drone() {

  ... # truncated
  newbie) # without quotes
      PX4_VERSION="v1.15.0"
      DRONE_FW_VERSION="0.0.1"

      VENDOR="px4"
      MODEL="fmu-v6x"
      ;;
  ... # truncated

}
```
To add a new drone **the following variables are mandatory*:
- `PX4_VERSION`: the version of the PX4 firmware to build.
- `DRONE_FW_VERSION`: the version of the custom firmware version.
- `VENDOR`: The manufacturer of the board. E.g. the vendor name for Pixhawk series boards is `px4`.
- `MODEL`: The board model. E.g. for a `px4` vendor a model might be `fmu-v3` or `fmu-v6x`, it clearly depends on the hardware, see [building px4 - build targets](https://docs.px4.io/main/en/dev_setup/building_px4.html#px4-make-build-targets) for some model options.

4. Create a board configuration file with the name `<DRONE_NAME>.px4board` under the folder `boards/<VENDOR>/<MODEL>/`. E.g. `boards/px4/fmu-v6x/newbie.px4board`.

5. In the previous created file `newbie.px4board` specifies the [modules](https://docs.px4.io/main/en/modules/modules_main.html) to enable and/or disable. For complete examples see the file [multicopter.px4board](https://github.com/PX4/PX4-Autopilot/blob/main/boards/px4/fmu-v6x/multicopter.px4board) in the official [`PX4-Autopilot`](https://github.com/PX4/PX4-Autopilot) repo as a reference use case.

6. Create a custom airframe file with the name `<UID>_eolab_<DRONE_NAME>` under `ROMFS/px4fmu_common/init.d/airframes/`. E.g. assuming an `UID` that **is unused** like `22110` we can create the file `ROMFS/px4fmu_common/init.d/airframes/22110_eolab_newbie` for the drone `newbie`. See the official documentation [Adding a Frame Configuration - Section: Configuration File Overview](https://docs.px4.io/main/en/dev_airframes/adding_a_new_frame.html#configuration-file-overview) for a full explanation on the format expected in this file.

> [!NOTE]
> As a convention eolab drones must be in the range of [22100 22199]. Check [`airframes.eolab`](./airframes.eolab) for the UID already in use.

7. In the previous created file `22110_eolab_newbie` set your parameters. E.g.:

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
#!/bin/sh

param set-default MAV_0_CONFIG 101
param set-default MAV_1_CONFIG 0

param set-default RC_CRSF_PRT_CFG 102
```

Note: see [PX4-Autopilot/ROMFS/px4fmu_common/init.d/airframes](https://github.com/PX4/PX4-Autopilot/tree/main/ROMFS/px4fmu_common/init.d/airframes) to check for already used `UID`.

8. Add the new airframe file to the [`airframes.eolab`](./airframes.eolab) file.

Done.
