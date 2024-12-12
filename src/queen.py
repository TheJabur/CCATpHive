# ============================================================================ #
# queen.py
# Control computer script to send commands to drones.
# James Burgoyne jburgoyne@phas.ubc.ca
# CCAT Prime 2022   
# ============================================================================ #



# ============================================================================ #
# IMPORTS
# ============================================================================ #

import os
import redis
import numpy as np
import logging
# import uuid
import pickle
from datetime import datetime
# import tempfile
import time
import signal

from config import queen as cfg
from config import parentDir

import queen_commands.control_io as io
import redis_channels as chans
import queen_commands.test_functions as test
import drone_control as drone_control



# ============================================================================ #
# CONFIG
# ============================================================================ #


logging.basicConfig(
    filename=f'{parentDir(__file__)}/logs/queen.log', level=logging.DEBUG,
    style='{', datefmt='%Y-%m-%d %H:%M:%S', 
    format='{asctime} {levelname} {filename}:{lineno}: {message}'
)


# ============================================================================ #
#  queen commands list
def _com():
    return {
        1:alcoveCommand,
        # 2:listenMode,
        3:getKeyValue,
        4:setKeyValue,
        5:getClientList,
        6:getClientListLight,
        7:drone_control.action,
        8:monitorMode,
        10:test.tonePowerTest,
        11:test.adriansNoiseTest,
        12:test.targetSweepPowerTest,
        # 13:test.targetSweepAndNoiseSweep,
    }



# ============================================================================ #
# COMMAND FUNCTIONS
# ============================================================================ #


# ============================================================================ #
# comList
def comList():
    """A list of all Queen command names (strings)."""

    return [com[key].__name__ for key in com.keys()]


# ============================================================================ #
# comNumFromStr
def comNumFromStr(com_str):
    """Command number (int) from command name (str)."""

    _print("comNumFromStr")
    coms = {com[key].__name__:key for key in com.keys()}
    _print(coms)
    return int(coms[com_str])


# ============================================================================ #
# _catchAllResponses
def _catchAllResponses(p, num_clients, timeout=120):
    """Listen for Redis responses, with a timeout.

    p: Redis pubsub object that listens for responses.
    num_clients (int): Number of responses to wait for.
    timeout (int): Timeout in seconds.

    Returns: (list) Collected responses.
    Raises: TimeoutError: If listening times out.
    """

    resps = [] # return list

    # nothing to listen for!
    if num_clients <= 0:
        return resps

    # initialize timeout handler
    def timeout_handler(signum, frame):
        raise TimeoutError("Listening timed out.")
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)

    try:
        for new_message in p.listen():

            # only care about pmessages
            if new_message['type'] != 'pmessage':
                continue 

            # process this return
            resps.append(new_message)
            _processCommandReturn(new_message['data'])  # print and save

            # stop when all expected returns received
            if len(resps) >= num_clients:
                break

    # stop listening and pass back on timeout
    except TimeoutError:
        pass
    finally:
        signal.alarm(0) # Disable the alarm

    return resps


# ============================================================================ #
#  alcoveCommand
def alcoveCommand(com_num, bid=None, drid=None, all_boards=False, args=None, timeout=120):
    '''Send an alcove command to given board[s].

    com_num: (int) Command number.
    bid: (int) Board identifier, optional.
    drid: (int) Drone identifier (1-4), optional. Requires bid to be set.
    all_boards: (bool) Send to all boards instead of bid/drid. Overrides bid.
    args: (str) Command arguments.
    timeout: (int) Timeout to wait for responses. [s]
    
    Return: 2-tuples (num_clients, ret_dict)
        num_clients: (int) Number of clients that received the command.
        ret_dict: (dict/None) Conglomerate return dictionary from all clients.
    '''

    to_str = "all boards" if all_boards else f"{bid}.{drid}" if drid else f"board {bid}"
    print(f"Attempting to send command ({com_num}) to {to_str} with args={args}.")

    ret = (0,[])  # default return

    if not all_boards and not bid:
        print("Command not sent: bid required if not sending to all boards.")
        return ret

    # all_boards overrides bid and drid
    if all_boards:
        bid, drid = None, None

    r,p = _connectRedis()

    # build payload for drone[s]
    payload = f'{com_num}' if args is None else f'{com_num} {args}'

    # build Redis command channels
    chan = chans.comChan(bid, drid)
        
    # subscribe for returns
    p.psubscribe(chan.subRet)

    # send the command
    num_clients = r.publish(chan.pub, payload) # send command
    if num_clients == 0:
        print(f"No client received this command!")
        return ret
    print(f"{num_clients} drones received this command.")

    # Listen for a responses
    # if a command takes longer than timeout it won't catch response
    print(f"Listening for responses... ", end="")
    resps = _catchAllResponses(p, num_clients, timeout=timeout)
    print(f"{len(resps)} received. Done.")

    ret = (num_clients, resps)
    return ret


# ============================================================================ #
#  callCom
def callCom(com_num, args=None, bid=None, drid=None):
    '''Execute a queen command function by key.

    com_num: (int) command number (see queen commands list).
    args: (str) arguments for command (see payloadToCom).
    '''

    ret = (0,[]) # default return

    # invalid command
    if com_num not in com:
        print('Invalid command: '+str(com_num))
        return ret

    # convert string args to standard arg/kwargs list/dict
    args, kwargs = _strToArgsAndKwargs(args)

    # add bid/drid to kwargs if present
    if bid: 
        kwargs['bid'] = bid
    if bid and drid: 
        kwargs['drid'] = drid

    # execute queen command
    resp = com[com_num](*args, **kwargs)

    ret = (0,[resp]) # format like alcoveCommand return
    return ret


# ============================================================================ #
#  monitorMode
def monitorMode():
    """Monitor/keep-alive the drones, as per the master drone list file.
    """

    # hold a Redis connection
    r,p = _connectRedis() # any problems with holding this for a long time?

    # action taken every monitor loop
    def monitorAction(r):

        # load needed drone lists
        drone_list = drone_control._droneList()      # master drone list
        client_list = drone_control._clientList()    # redis client list
        override_list = drone_control._loadOvRide()  # tmp override list

        # loop over master drone list
        for id in drone_list:

            bid, drid = drone_control._bid_drid(id)

            # ignore if on override list
            if drone_control._hasOvRide(bid, drid, override_list):
                continue

            # check if drone running, start if not
            status = drone_control._monitorDrone(
                bid, drid, drone_list, client_list, r=r)
            
            if status: # not 0
                msg = f"monitorMode: "
                if status == 1:
                    msg += "Starting "
                elif status == 2:
                    msg += "Stopping "
                else:
                    msg += "Unknown status: "
                msg += f"drone {id}."
                print(msg) # queen logs prints
                _notificationHandler(msg)

    # monitor loop
    print('Starting queen monitor mode.') 
    while True:
        monitorAction(r)
        time.sleep(cfg.monitor_interval) 


# ============================================================================ #
#  listenMode
"""
def listenMode():
    '''Listen for Redis messages (threaded).
    '''
    # CTRL-C to exit listening mode

    r,p = _connectRedis()

    def handleMessage(message):
        '''actions to take on receiving message'''
        if message['type'] == 'pmessage':
            # print(message['data'].decode('utf-8')) # log/print message
            # _notificationHandler(message)  # send important notifications
            print(f"{_timeMsg()} Message received on channel: {message['channel']}")
            try:
                _processCommandReturn(message['data'])
            except Exception as e: 
                return _fail(e, f'Failed to process a response.')
            
    # Message received: {'type': 'pmessage', 'pattern': b'rets_*', 'channel': b'rets_board_1.1_f9af519c-bea0-4093-81cf-8f8a423dc549', 'data': b'\x80 ...

    rets_chan = rc.getAllReturnsChan()
    p.psubscribe(**{rets_chan:handleMessage})
    thread = p.run_in_thread(sleep_time=2) # move listening to thread
        # sleep_time is a socket timeout
         # too low and it will bog down server
         # can be set to None but may cause issues
         # more research is recommended
    print('The Queen is listening...') 

    # This thread isn't shut down - could lead to problems
    # thread.stop()
    return thread
"""


# ============================================================================ #
#  get/setKeyValue
def getKeyValue(key):
    """
    GET the value of given key.
    """

    r,p = _connectRedis()
    ret = r.get(bytes(key, encoding='utf-8'))
    ret = None if ret is None else ret.decode('utf-8')

    print(ret) # log/print message
    _notificationHandler(ret)  # send important notifications

def setKeyValue(key, value):
    """
    SET the given value for the given key.
    """

    r,p = _connectRedis()
    r.set(bytes(key, encoding='utf-8'), bytes(value, encoding='utf-8'))   


# ============================================================================ #
#  getClientList
def getClientList(do_print=True):
    """Print the Redis client list.
    do_print: (bool) prints list if True, else returns.
    """
    # args are string only
    do_print = False if not do_print or do_print=='False' else True

    r,p = _connectRedis()

    client_list = r.client_list()

    if do_print:
        print("START CLIENT LIST", "="*20)
        for client in client_list:
            # client_address = f"{client['addr']}:{client['port']}"
            client_address = f"{client['addr']}"
            client_name = client.get('name', 'N/A')
            print(f"Client: {client_address} {client_name}")
        print("END CLIENT LIST", "="*22)

    return client_list


# ============================================================================ #
#  getClientListLight
def getClientListLight():
    """Print the Redis client list.
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
# INTERNAL FUNCTIONS
# ============================================================================ #


# ============================================================================ #
#  print monkeypatch
_print = print 
def print(*args, **kw):
    
    # _print(*args, **kw) # print to terminal
    # terminal printing can cause issues with asynchronous tasks

    args = [str(arg) for arg in args] # not all args are str, so cast
    msg = ' '.join(args) # convert to a single str
    msg = msg.strip() # remove trailing space
    logging.info(msg) # output to log


# ============================================================================ #
#  _success/_fail
# def _success(msg):
#     print("Done.")
#     if msg is not None: logging.info(msg)

# def _fail(e, msg=None):
#     print("Failed.")
#     if msg is not None: logging.info(msg)
#     logging.error(e)
#     return e


# ============================================================================ #
#  _connectRedis
def _connectRedis():
    '''connect to redis server'''

    r = redis.Redis(host=cfg.host, port=cfg.port, db=cfg.db, password=cfg.pw)
    p = r.pubsub()

    r.client_setname(f'queen')

    # check for connection
    try:
        r.ping()
    except redis.exceptions.ConnectionError as e:
        print(f"Redis connection error: {e}")

    return r, p


# ============================================================================ #
#  _processCommandReturn
def _processCommandReturn(dat):
    '''Process the return data from a command.'''

    d = pickle.loads(dat)             # assuming msg is pickled
    
    if isinstance(dat, str):          # print if string
        print(dat) 

    try:
        io.saveWrappedToTmp(d)        # save a wrapped return
    except:
        io.saveToTmp(dat)             # or save as tmp


# ============================================================================ #
#  _notificationHandler
def _notificationHandler(message):
    '''process given messages for sending notifications to end-users'''

    print(f"notificationHandler(): Not implemented yet. Message: {message}")
    # todo
     # look through given message[s?]
     # and look through configured notifications
     # and send emails as appropriate


# ============================================================================ #
#  _timeMsg
def _timeMsg():
    """A clear and concise time string for print statements."""

    fmt = "%H:%M:%S_%y%m%d"

    time_now = datetime.now()
    time_str = time_now.strftime(fmt)
    # ms_str = f".{time_now.microsecond // 1000:03}"
    
    return time_str


# ============================================================================ #
#  _strToArgsAndKwargs
def _strToArgsAndKwargs(args_str=''):
    '''Convert string arguments to stanard args/kwargs list/dict.

    args_str: (str) Arguments string, e.g. 'arg1=val1, arg2=val2'.
    '''

    # convert None to blank str
    if not args_str:
        args_str = ''

    # cleanup string formatting (user inputted)
    args_str = args_str.replace(",", " ")
    args_str = args_str.replace("=", " = ")
    args_str = ' '.join(args_str.split()) # remove excess whitespace
    l = args_str.split()
    
    # build args and kwargs
    args = []
    kwargs = {}
    while len(l)>0:
        e = l.pop(0)

        # named kwarg
        if len(l)>0 and l[0]=='=':
            l.pop(0) # get rid of =
            kwargs[e] = l.pop(0)

        # positional arg
        else: 
            args.append(e)

    return args, kwargs




# ============================================================================ #
# INIT
# ============================================================================ #
 

com = _com()