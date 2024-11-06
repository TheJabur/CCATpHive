## Queen configuration file
## which lives on the control server

## redis server configuration
host = 'localhost'
# host = '192.168.2.80'
port = 6379
db   = 0
pw   = None

## RFSoC SSH credentials
# this could be changed so the boards are given 
# the control computer public key instead
ssh_user = 'xilinx'
ssh_pass = 'xilinx'

## master drone list
master_drone_list_file = 'master_drone_list.yaml'