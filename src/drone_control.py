# ============================================================================ #
# drone_control.py
# Queen drone control script (start/stop/restart).
# James Burgoyne jburgoyne@phas.ubc.ca 
# CCAT Prime 2024 
# ============================================================================ #



# ============================================================================ #
# IMPORTS & GLOBALS
# ============================================================================ #

import redis

from config import queen as cfg
import queen_commands.control_io as io



# ============================================================================ #
# INTERNAL FUNCTIONS
# ============================================================================ #


# ============================================================================ #
# _bid_drid
def _bid_drid(id):
    '''Separate id into bid.drid.
    Returns int (bid, drid), (bid, None), or (None, None).

    id: (str) in format 'bid.drid' or 'bid'.
    '''

    import re

    # casting from Redis strings
    id  = str(id)
    
    if re.fullmatch(r'\d+(\.\d+)?', id): # enforce 'x.y' or 'x'

        parts = id.split('.')
        bid = int(parts[0])
        drid = int(parts[1]) if len(parts) > 1 else None
        
    else: # incorrect format
        bid, drid = None, None

    return bid, drid


def _id(bid, drid=None):
    '''Join bid.drid into id.
    '''

    id = f"{bid}.{drid}"

    # check for consistency
    bidc, dridc = _bid_drid(id)
    if bidc != bid or dridc != drid:
        id = None

    return id


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

    id = _id(bid, drid)

    # get master drone list unless it was passed in
    if drone_list is None:
        drone_list = _droneList()

    # get drone properties from list
    drone_props = drone_list.get(id)

    return drone_list, drone_props


# ============================================================================ #
#  _connectRedis
def _connectRedis():
    '''Connect to the redis server.
    '''

    r = redis.Redis(host=cfg.host, port=cfg.port, db=cfg.db, password=cfg.pw)
    p = r.pubsub()

    r.client_setname(f'drone_control')

    # check for connection
    try:
        r.ping()
    except redis.exceptions.ConnectionError as e:
        print(f"Redis connection error: {e}")

    return r, p


# ============================================================================ #
#  _clientList
def _clientList():
    """The Redis client list.
    """

    r,p = _connectRedis()

    client_list = r.client_list()

    props = ['name', 'addr', 'age']
    client_list_light = {}
    for client in client_list:
        client_list_light[client['id']] = {
            prop: client.get(prop, 'N/A')
            for prop in props
        }

    return client_list_light


# ============================================================================ #
# _droneRunning
def _droneRunning(bid, drid):
    '''Check if drone is running by checking if it's in Redis client list.
    '''

    id = _id(bid, drid)

    client_list = _clientList()

    return id in client_list


# ============================================================================ #
# _sshExe
def _sshExe(ip, command):
    '''Execute a command via SSH on RFSoC at IP.
    '''

    import paramiko

    # Set up SSH client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
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

        stdin.close()

    except Exception as e:
        print(f"An error occurred with {ip}: {e}")
    
    # Close the connection
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

    if action not in ['start', 'stop', 'restart', 'status', 
                      'startAllDrones', 'stopAllDrones', 'restartAllDrones']:
        return None

    if action == 'start':
        return startDrone(bid, drid, drone_list)

    if action == 'stop':
        return stopDrone(bid, drid, drone_list)

    if action == 'restart':
        return restartDrone(bid, drid, drone_list)

    if action == 'status':
        return statusDrone(bid, drid, drone_list)

    if action == 'startAllDrones':
        return startAllDrones()

    if action == 'stopAllDrones':
        return stopAllDrones()

    if action == 'restartAllDrones':
        return restartAllDrones()


# ============================================================================ #
# startDrone
def startDrone(bid, drid, drone_list=None, check=False):
    '''Start the drone at bid.drid if not running.
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
    '''Stop the drone bid.drid if running.
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
    '''Restart the drone bid.drid, whether running or not.
    '''

    drone_list, drone_props = _droneListAndProps(bid, drid, drone_list)
    
    # check for drone in master list
    if drone_props is None:
        print(f"Drone {bid}.{drid} not in master drone list.")
        return
    
    # stop the drone
    print(f"Restarting drone {bid}.{drid}... ", end="", flush=True)
    command = f"sudo systemctl restart drone@{drid}.service"
    ret = _sshExe(drone_props['ip'], command)
    print("Done.")

    return ret


# ============================================================================ #
# statusDrone
def statusDrone(bid, drid, drone_list=None):
    '''
    '''

    drone_list, drone_props = _droneListAndProps(bid, drid, drone_list)
    
    # check for drone in master list
    if drone_props is None:
        print(f"Drone {bid}.{drid} not in master drone list.")
        return

    id = _id(bid, drid)

    # basic drone master list properties
    ip = drone_props.get('ip')
    to_run = drone_props.get('to_run')

    # drone is running
    client_list = _clientList()
    print(client_list)
    is_running = f"drone_{id}" in client_list

    # status message
    msg = f"Status: Drone {id}: ip={ip}, to_run={to_run}, running={is_running}"
    
    print(msg)
    # return msg


# ============================================================================ #
# startAllDrones
def startAllDrones():
    '''Start all drones in master drone list (if to_run=True).
    '''
    
    # load the master drone list
    drone_list = _droneList()

    # iterate through row by row
    for id, props in drone_list.items():

        # skip this drone if it's not supposed to be running
        if props.get('to_run') != True:
            continue

        bid, drid = _bid_drid(id)

        # start drone
        startDrone(bid=bid, drid=drid, drone_list=drone_list)      


# ============================================================================ #
# stopAllDrones
def stopAllDrones():
    '''Stop all drones in master drone list (if running).
    '''
    
    # load the master drone list
    drone_list = _droneList()

    # iterate through row by row
    for id, props in drone_list.items():

        bid, drid = _bid_drid(id)

        # stop drone
        stopDrone(bid=bid, drid=drid, drone_list=drone_list)


# ============================================================================ #
# restartAllDrones
def restartAllDrones():
    '''Restart all drones in master drone list.
    '''
    
    # load the master drone list
    drone_list = _droneList()

    # iterate through row by row
    for id, props in drone_list.items():

        bid, drid = _bid_drid(id)

        # stop drone
        restartDrone(bid=bid, drid=drid, drone_list=drone_list)
