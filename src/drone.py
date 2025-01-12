# ============================================================================ #
# drone.py
# Board side Redis interface script.
# James Burgoyne jburgoyne@phas.ubc.ca
# CCAT/FYST 2024 
# ============================================================================ #



# ============================================================================ #
# IMPORTS
# ============================================================================ #


import os
import sys
import redis
import shutil
import pickle
import logging
import argparse
import importlib


import alcove
from config import board as cfg_b
import redis_channels as chans




# ============================================================================ #
# MAIN
# ============================================================================ #


def main():
    # CTRL-c to exit out of listen mode

    # only modify log if this is main
    logging.basicConfig(
        filename='../logs/board.log', level=logging.DEBUG,
        style='{', datefmt='%Y-%m-%d %H:%M:%S', 
        format='{asctime} {levelname} {filename}:{lineno}: {message}'
    )

    # setup and get the CLI args
    args = _setupArgparse() 

    # modify the configs as necessary
    _modifyConfig(args)

    # setup a drone sepcific dir in /tmp
    _setupTmpDir()

    # load firmware to config
    _loadFirmware()

    # connect to Redis server and establish connection objects
    r,p = connectRedis()
    r.client_setname(f'drone_{cfg_b.bid}.{cfg_b.drid}')

    print(f"Drone {cfg_b.bid}.{cfg_b.drid} is running...")

    # run loop
    listenMode(r, p, chans.subList(cfg_b.bid, cfg_b.drid))

            


# ============================================================================ #
# INTERNAL FUNCTIONS
# ============================================================================ #


# ============================================================================ #
# print monkeypatch
_print = print 
def print(*args, **kw):
    '''Override the print statement.
    '''
    
    msg = ""

    # add drone id
    if cfg_b.bid and cfg_b.drid:
        # msg += f"drone={cfg_b.bid}.{cfg_b.drid}: "
        msg += f"{cfg_b.bid}.{cfg_b.drid}: "

    # add current filename
    # msg += f"{os.path.basename(__file__)}: "

    # add print strings
    msg += " ".join(map(str, args))

    # log msg
    logging.info(msg)

    # print to console
    _print(msg, **kw)


# ============================================================================ #
# _setupArgparse
def _setupArgparse():
    '''Setup the argparse arguments'''

    parser = argparse.ArgumentParser(
        description='Terminal interface to drone script.')

    # add arguments
    parser.add_argument(                # positional, required, 1-4
        "drid", type=int, help="drone id", choices=range(1,4+1))
   
    # return arguments values
    return parser.parse_args()


# ============================================================================ #
# _modifyConfig
def _modifyConfig(args):
    '''modify config level variables'''

    # project root directory (src)
    cfg_b.src_dir = os.getcwd()          # assuming this file lives in root dir

    # parent directory
    par_dir = os.path.realpath(os.path.pardir)

    # drone directory
    cfg_b.drone_dir = f'{par_dir}/drones/drone{args.drid}'

    # tmp directory
    cfg_b.temp_dir = f'/tmp/drone{args.drid}'

    # drone config
    sys.path.append(cfg_b.drone_dir)
    cfg_dr = importlib.import_module(f'_cfg_drone{args.drid}')

    # drone identifier
    cfg_b.drid = cfg_dr.drid


# ============================================================================ #
# _setupTmpDir
def _setupTmpDir():
    '''Setup the system tmp directory to use.
    '''

    d = cfg_b.temp_dir

    # Ensure the custom directory is fresh
    if os.path.exists(d):
        shutil.rmtree(d)  # Delete the existing directory
    os.makedirs(d)        # Create a fresh directory

    # Set the TMPDIR environment variable
    os.environ["TMPDIR"] = d


# ============================================================================ #
# _loadFirmware
def _loadFirmware():

    try:
        from pynq import Overlay # type: ignore

        firmware_file = os.path.join(cfg_b.dir_root, cfg_b.firmware_file)
        cfg_b.firmware = Overlay(firmware_file, ignore_version=True, download=False)

    except Exception as e: 
        firmware = None


# ============================================================================ #
# connectRedis
def connectRedis():
    '''connect to redis server'''
    r = redis.Redis(host=cfg_b.host, port=cfg_b.port, db=cfg_b.db, password=cfg_b.pw)
    p = r.pubsub()

    # check for connection
    try:
        r.ping()
    except redis.exceptions.ConnectionError as e:
        print(f"Redis connection error: {e}")

    return r, p


# ============================================================================ #
# listenMode
def listenMode(r, p, chan_subs):
    p.psubscribe(chan_subs)             # channels to listen to

    last_chan_str = ''

    for new_message in p.listen():      # infinite listening loop
        # print(new_message)

        # check this is a command
        if new_message['type'] != 'pmessage':
            continue

        # get channel string (unique to command)
        chan_str = new_message['channel'].decode('utf-8')
        # cid = chan_sub.split('_')[-1]    # recover cid from channel

        # check we haven't already processed this message
        # e.g. could have come through on another channel
        if chan_str == last_chan_str:
            continue
        last_chan_str = chan_str

        payload = new_message['data'].decode('utf-8')
        try:
            com_num, ret_data, args, kwargs = payloadToCom(payload)
            # print(com_num, args, kwargs)
            com_ret = executeCommand(com_num, ret_data, args, chan_str, kwargs)
        except Exception as e:
            com_ret = f"Payload error ({payload}): {e}"
            print(com_ret)
        
        # publishResponse(com_ret, r, bid, cid) # send response
        publishResponse(com_ret, r, chan_str) # send response


# ============================================================================ #
# executeCommand
def executeCommand(com_num, ret_data, args, chan_str, kwargs):
    '''
    ret_data: (bool) Whether to return data from command func.
    '''

    print(f"Exe com {com_num} (chan: {chan_str} args={args})")

    # execute the command
    try:
        ret = alcove.callCom(com_num, args, kwargs)

    # command execution failed
    except Exception as e:
        ret = f"Command execution error: {e}"
        print(f" Command {com_num} execution failed.")

    # command execution successful
    else:
        if ret is None or not ret_data:
            ret = f"Command {com_num} executed." # success ack.
        # print(f" Command {com_num} execution done.")

    return ret


# ============================================================================ #
# publishResponse
def publishResponse(resp, r, chan_str):
    '''Publish a response on return channel.
    '''

    chan = chans.comChan(chan=chan_str)
    # print(f" {chan.pubRet}")

    try: 
        ret = pickle.dumps(resp) # convert to bytes object; required by Redis
        r.publish(chan.pubRet, ret) # publish resp with Redis on return channel

    except Exception as e:
        print(f' Publish response failed.')
    else:
        # print(f' Publish response successful.')
        pass


# ============================================================================ #
# listToArgsAndKwargs
def listToArgsAndKwargs(args_list):
    """Split an arg list into args and kwargs.
    l: Args list to split.
    Returns args (list) and kwargs (dictionary)."""
    
    args_str = ' '.join(args_list)
    args_str = args_str.replace(",", " ")
    args_str = args_str.replace("=", " = ")
    args_str = ' '.join(args_str.split()) # remove excess whitespace
    l = args_str.split()
    
    args = []
    kwargs = {}
    while len(l)>0:
        v = l.pop(0)

        if len(l)>0 and l[0]=='=': # kwarg
            l.pop(0) # get rid of =
            kwargs[v] = l.pop(0)

        else: # arg
            args.append(v)

    return args, kwargs


# ============================================================================ #
# payloadToCom
def payloadToCom(payload):
    """
    Convert payload to com_num, args, kwargs.
        payload: Command string data.
            Payload format: [com_num] [positional arguments] [named arguments].
            Named arguments format: -[argument name] [value].
    """
    
    paylist = payload.split()
    com_num = int(paylist.pop(0)) # assuming first item is com_num
    ret_data = int(paylist.pop(0)) # assuming second item is ret_data
    args, kwargs = listToArgsAndKwargs(paylist)
    
    return com_num, ret_data, args, kwargs


# ============================================================================ #
# get/setKeyValue
def getKeyValue(key):
    """
    GET the value of given key.
    """

    r,p = connectRedis()
    ret = r.get(bytes(key, encoding='utf-8'))
    ret = None if ret is None else ret.decode('utf-8')

    return ret

def setKeyValue(key, value):
    """
    SET the given value for the given key.
    """

    r,p = connectRedis()
    r.set(bytes(key, encoding='utf-8'), bytes(value, encoding='utf-8'))   



# ============================================================================ #
# MAIN
# ============================================================================ #


if __name__ == "__main__":
    main()