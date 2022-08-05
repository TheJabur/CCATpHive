########################################################
### Remote-side Redis interface.                     ###
### Interfaces with redis-client to execute alcove   ###
### commands from queen.                             ###
###                                                  ###
### James Burgoyne jburgoyne@phas.ubc.ca             ###
### CCAT Prime 2022                                  ###
########################################################



###############
### IMPORTS ###


import alcove
import redis
import os
import sys
import importlib
import logging
import pickle
import argparse

import _cfg_board as cfg
# import _cfg_drone done in main()



##############
### CONFIG ###

logging.basicConfig(
    filename='logs/board.log', level=logging.DEBUG,
    style='{', datefmt='%Y-%m-%d %H:%M:%S', 
    format='{asctime} {levelname} {filename}:{lineno}: {message}'
)



######################
### MAIN EXECUTION ###


def main():   

    args = setupArgparse()              # get command line arguments

    modifyConfig(args)

    # droneConfig(args.drid)              # process drone config
    
    # import _cfg_drone.py as cfg_dr      # import drone config module
    # cfg.drid = cfg_dr.drid              # update drone identifier in config

    drid = cfg.drid                     # drone identifier
    bid = cfg.bid                       # board identifier
    chan_subs = [                       # listening channels
        f'board_{bid}_*',               # this boards listening channels
        'all_boards']                   # an all-boards listening channel

    r,p = connectRedis()                # redis and pubsub objects

    listenMode(r, p, bid, chan_subs)    # listen for redis messages
    # currently, only way to exit out of listen mode is CTRL-c
            


##########################
### INTERNAL FUNCTIONS ###


# monkeypatch the print statement
# the print statement should be further modified
# to save all statements into a log file
_print = print 
def print(*args, **kw):
    # add current filename in front
    _print(f"{os.path.basename(__file__)}: ", end='')
    _print(*args, **kw)


def setupArgparse():
    '''Setup the argparse arguments'''

    parser = argparse.ArgumentParser(
        description='Terminal interface to drone script.')

    # add arguments
    parser.add_argument(                # positional, required, 1-4
        "drid", type=int, help="drone id", choices=range(1,4+1))
   
    # return arguments values
    return parser.parse_args()


def modifyConfig(args):
    '''modify config level variables'''

    ## project root directory
    cfg.root_dir = os.getcwd()          # assuming this file lives in root dir

    ## drone config
    drid = args.drid
    sys.path.append(f'{cfg.root_dir}/drones/drone{drid}')
    cfg_dr = importlib.import_module(f'_cfg_drone{drid}')
    cfg.drid = cfg_dr.drid              # update drone identifier in config


def connectRedis():
    '''connect to redis server'''
    r = redis.Redis(host=cfg.host, port=cfg.port, db=cfg.db)
    p = r.pubsub()
    return r, p


def listenMode(r, p, bid, chan_subs):
    p.psubscribe(chan_subs)             # channels to listen to
    for new_message in p.listen():      # infinite listening loop
        print(new_message)              # output message to term/log

        if new_message['type'] != 'pmessage': # not a command
            continue                    # skip this message

        channel = new_message['channel'].decode('utf-8')
        cid = channel.split('_')[-1]    # recover cid from channel

        payload = new_message['data'].decode('utf-8')
        try:
            com_num, args, kwargs = payloadToCom(payload) # split payload into command
            print(com_num, args, kwargs)
            com_ret = executeCommand(com_num, args, kwargs) # attempt execution
        except Exception as e:
            com_ret = f"Payload error ({payload}): {e}"
            print(com_ret)
        
        publishResponse(com_ret, r, bid, cid) # send response


def executeCommand(com_num, args, kwargs):
    print(f"Executing command: {com_num}... ")
    try: #####
        ret = alcove.callCom(com_num, args, kwargs)   # execute the command

    except Exception as e:              # command execution failed
        ret = f"Command execution error: {e}"
        print(f"Command {com_num} execution failed.")
        logging.info('Command {com_num} execution failed.')

    else:                               # command execution successful
        if ret is None:                 # default return is None (success)
            ret = f"Command {com_num} executed." # success ack.
        print(f"Command {com_num} execution done.")
        logging.info(f'Command {com_num} execution successful.')

    return ret


def publishResponse(resp, r, bid, cid):
    chanid = f'{bid}_{cid}'             # rebuild chanid
    chan_pubs = f'board_rets_{chanid}'  # talking channel

    print(f"Preparing response... ", end="")
    try: #####
        ret = pickle.dumps(resp)        # pickle serializes to bytes obj.
        # this is needed because redis pubsub only allows bytes objects
    except Exception as e:
        _print("Failed.")
        logging.info(f'Publish response failed.')
        return                          # exit: need ret to send
    else:
        _print("Done.")

    print(f"Sending response... ", end="")
    try: #####
        r.publish(chan_pubs, ret)       # publish with redis
    except Exception as e:
        _print("Failed.")
        logging.info(f'Publish response failed.')
    else:
        _print(f"Done.")
        logging.info(f'Publish response successful.')


def listToArgsAndKwargs(l):
    '''Split a list into args and kwargs.
    l: List to split.
    Returns args (list) and kwargs (dictionary).'''

    args = []
    kwargs = {}
    while len(l)>0:
        v = l.pop(0)

        # if this doesn't have a dash in front
        # or theres no more items
        # or the next item has a dash in front
        if v[0]!='-' or len(l)==0 or l[0][0]=='-':
            args.append(v)             # then this is an arg

        else:
            v = v.lstrip('-')          # remove dashes in front
            kwargs[v] = l.pop(0)       # this is a kwarg

    return args, kwargs


def payloadToCom(payload):
    '''Convert payload to com_num, args, kwargs.
    payload: Command string data.
        Payload format: [com_num] [positional arguments] [named arguments].
        Named arguments format: -[argument name] [value].'''
    
    paylist = payload.split()
    com_num = int(paylist.pop(0)) # assuming first item is com_num
    args, kwargs = listToArgsAndKwargs(paylist)
    
    return com_num, args, kwargs



if __name__ == "__main__":
    main()