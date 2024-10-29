#!/bin/bash
# set -x

# Store the drone number from the argument
DRONE_NUMBER=$1

# Become root and run commands in bash explicitly
sudo bash <<EOF
# Source the environment
source /home/xilinx/xilinx/activate

# Change to the directory containing drone.py
cd /home/xilinx/primecam_readout/src

# Add the directory containing _cfg_drone1 to the PYTHONPATH if needed
#export PYTHONPATH=\$PYTHONPATH:/home/xilinx/primecam_readout/src

# Run the drone.py script with the drone number as an argument
exec /usr/local/share/pynq-venv/bin/python3 /home/xilinx/primecam_readout/src/drone.py $DRONE_NUMBER
EOF