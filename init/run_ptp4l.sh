#!/bin/bash
interface=$1
mac_address=$2

# Determine the directory where this script is located
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Kill existing ptp4l processes
killall ptp4l

# Run ptp4l with the specified interface and MAC address
#ptp4l -i $interface -f gPTP.cfg --step_threshold=1 -p $mac_address &
ptp4l -i "$interface" -f "$script_dir/gPTP.cfg" --step_threshold=1 &
