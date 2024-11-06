# ============================================================================ #
# drone_control.py
# Queen drone control script (start/stop/restart).
# James Burgoyne jburgoyne@phas.ubc.ca 
# CCAT Prime 2024 
# ============================================================================ #



# ============================================================================ #
# IMPORTS & GLOBALS
# ============================================================================ #

# import os
import logging
logging.getLogger("paramiko").setLevel(logging.CRITICAL)

from config import queen as cfg
import queen_commands.control_io as io



# ============================================================================ #
# INTERNAL FUNCTIONS
# ============================================================================ #


# ============================================================================ #
# _droneList
def _droneList():
    '''Get the drone list from the master drone list file.
    '''
    
    import yaml, os

    master_drone_list_file = os.path.join(cfg.dir_root, 
                                          cfg.master_drone_list_file)
    with open(master_drone_list_file, "r") as file:
        drone_list = yaml.safe_load(file)

    return drone_list


# ============================================================================ #
# _droneListAndProps
def _droneListAndProps(bid, drid, drone_list=None):  
    '''Get master drone list and properties for given drone id.
    '''   

    # get master drone list unless it was passed in
    if drone_list is None:
        drone_list = _droneList()

    # get drone properties from list
    id = f"{bid}.{drid}"
    drone_props = drone_list.get(id)

    return drone_list, drone_props


# ============================================================================ #
# _droneRunning
def _droneRunning(bid, drid):
    # TODO: check if the drone is running... client list?
    return False


# ============================================================================ #
# _sshExe
def _sshExe(ip, command):
    '''Execute a command via SSH on RFSoC at IP.
    '''

    import paramiko

    # Set up SSH client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # try:
    # connect to board
    client.connect(hostname=ip, 
                    username=cfg.ssh_user, password=cfg.ssh_pass)

    # Execute the command
    stdin, stdout, stderr = client.exec_command(command)
    
    # Capture command output and errors
    output = stdout.read().decode()
    errors = stderr.read().decode()

    # Print or log output/errors as needed
    # if output:
    #     print(f"Output from {ip}:\n{output}")
    if errors:
        print(f"Errors from {ip}:\n{errors}")

    # except Exception as e:
    #     print(f"An error occurred with {ip}: {e}")
    
    # finally:
    #     # Close the connection
    client.close()




# ============================================================================ #
# COMMANDS
# ============================================================================ #


# TODO: modify redis tcp_keepalive ~ 10 s (and put in docs)


# TODO: create new mode in queen.py: queenMonitor
# fold queenListen into new mode
    # run startAllDrones when it begins
    # have it actively monitor and restart etc drones as necessary
    # monitor from client list


# ============================================================================ #
# action
def action(action, bid=None, drid=None, drone_list=None):
    '''Convenience function to commands.
    '''

    if action not in ['start', 'stop', 'restart', 'status']:
        return None

    if action == 'start':
        return startDrone(bid, drid, drone_list)

    if action == 'stop':
        return stopDrone(bid, drid, drone_list)

    if action == 'restart':
        return restartDrone(bid, drid, drone_list)

    if action == 'status':
        return statusDrone(bid, drid, drone_list)


# ============================================================================ #
# startDrone
def startDrone(bid, drid, drone_list=None, check=False):
    '''Start the drone at bid.drid.
    '''

    drone_list, drone_props = _droneListAndProps(bid, drid, drone_list)
    
    # check for drone in master list
    if drone_props is None:
        print(f"Drone {bid}.{drid} not in master drone list.")
        return

    # check if drone is already obviously running
    if check and _droneRunning(bid, drid):
        print(f"Drone {bid}.{drid} is already running.")
        return
    
    # start the drone
    print(f"Starting drone {bid}.{drid}... ", end="", flush=True)
    command = f"sudo systemctl start drone@{drid}.service"
    ret = _sshExe(drone_props['ip'], command)
    print("Done.")

    return ret


# ============================================================================ #
# stopDrone
def stopDrone(bid, drid, drone_list=None, check=False):
    '''Stop the drone bid.drid.
    '''

    drone_list, drone_props = _droneListAndProps(bid, drid, drone_list)
    
    # check for drone in master list
    if drone_props is None:
        print(f"Drone {bid}.{drid} not in master drone list.")
        return

    # check if drone is obviously running
    if check and not _droneRunning(bid, drid):
        print(f"Drone {bid}.{drid} is not running.")
        return
    
    # stop the drone
    print(f"Stopping drone {bid}.{drid}... ", end="", flush=True)
    command = f"sudo systemctl stop drone@{drid}.service"
    ret = _sshExe(drone_props['ip'], command)
    print("Done.")

    return ret


# ============================================================================ #
# restartDrone
def restartDrone(bid, drid, drone_list=None):
    # TODO:
    # what does the service do if its not running?
    # presumably want to start if not running
    # is this command even necessary?
    pass


# ============================================================================ #
# statusDrone
def statusDrone(bid, drid, drone_list=None):
    # TODO:
    # just client list status, or serviced status?
    # how would it get serviced status?
    pass


# TODO:
# 'All' in this context needs to be clear that it means from master drone list file
def startAllDrones():
    # parse master drone list file
    # and start all the drones in it
    # what if they are already running?
        # push problem to startDrone?
    pass


# TODO:
def stopAllDrones():
    pass


# TODO:
def restartAllDrones():
    pass
