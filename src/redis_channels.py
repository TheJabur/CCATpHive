# ============================================================================ #
# redis_channels.py
# Module to produce Redis channels.
# James Burgoyne jburgoyne@phas.ubc.ca
# CCAT/FYST 2024
# ============================================================================ #
# ============================================================================ #
# redis_channels.py
# Module to produce Redis channels.
# James Burgoyne jburgoyne@phas.ubc.ca
# CCAT/FYST 2024
# ============================================================================ #

import uuid

# try: from config import board as cfg_b
# except ImportError: cfg_b = None 




# ============================================================================ #
# _id
def _id(bid, drid):
    '''Build id string from bid and drid.

    bid: (int) Board identifier.
    drid: (int) Drone identifier {1,4}.
    '''

    id = None
    if bid:
        id = f'{bid}'        # e.g. '1'
        if drid:
            id += f'.{drid}' # e.g. '1.1'

    return id


# ============================================================================ #
# _bidDrid
def _bidDrid(id):
    '''Recover the bid and drid from the id.

    id: (str) bid.drid identifier.
    '''

    bid = None
    drid = None
    if id:
        words = str(id).split('.')
        bid = words[0]
        if len(words) > 1:
            drid = words[1]

    return bid, drid


# ============================================================================ #
# _pubChan
def _pubChan(bid=None, drid=None, cid=None, ret=False):
    '''Redis publish channel.

    bid: (int) Board identifier.
    drid: (int) Drone identifier {1,4}.
    cid: (str) Unique channel identifier.
    ret: (bool) Whether this is a return channel or not.
    '''

    chan = 'board'

    id = _id(bid, drid)

    if id:
        chan += f'_{id}'      # e.g. board_1 or board_1.1
    else:
        chan += '_all'        # e.g. board_all

    if cid:
        chan += f'_{cid}' # e.g. board_all_16fd2706-8baf-433b-82eb-8c7fada847da

    if ret:
        chan = f'rets_{chan}' # e.g. rets_board_1.1

    return chan


# ============================================================================ #
# _subChan
def _subChan(bid=None, drid=None, cid=None, ret=False, wildcard=True):
    '''Redis subscribe channel.

    bid: (int) Board identifier.
    drid: (int) Drone identifier {1,4}.
    cid: (str) Unique channel identifier.
    ret: (bool) Whether this is a return channel or not.
    wildcard: (bool) Will wildcard catch all sub channels.
        e.g. bid=1 will catch all channels to any drone on board 1.
    '''

    chan = f'{_pubChan(bid, drid, cid, ret)}'

    if wildcard:
        chan = f'{chan}_*'

    return chan


# ============================================================================ #
# _genChanParts
def _genChanParts(bid, drid):
    '''Generate all parts for chan (bid, drid, id, cid).

    bid: (int) Board identifier.
    drid: (int) Drone identifier {1,4}.
    '''

    id = _id(bid, drid)
    
    cid = str(uuid.uuid4())

    return bid, drid, id, cid


# ============================================================================ #
# _recoverChanParts
def _recoverChanParts(chan):
    '''Recover chan parts from chan string.

    chan: (str) Channel name.
    '''

    # remove wildcard if present
    if chan.endswith('*'):
        chan = chan[:-1]

    # split the chan into parts, assuming '_' is separartor
    words = chan.split('_')

    # get the default chan words
    base_words = _pubChan(ret=True).split('_') # ['rets','board','all']

    # remove 'rets' if it exists
    if words[0] == base_words[0]:
        words = words[1:]

    # get cid if it exists
    cid = None
    if len(words[-1]) == 36: # UUID4 always 36 chars 
        cid = words.pop()

    # bid and drid
    bid = None
    drid = None
    id = None
    if words[1] != base_words[2]: # not 'all'
        id = words[1]
        bid, drid = _bidDrid(id)

    return bid, drid, id, cid


# ============================================================================ #
# comChan class
class comChan:
    def __init__(self, bid:int=None, drid:int=None, chan:str=None):
        '''Produce all the pub and sub chan names and details.

        bid: (int) Board identifier.
        drid: (int) Drone identifier {1,4}.
        chan: (str) Channel name. Ignore bid and drid if given.
        '''

        # casting inputs
        bid = int(bid) if bid else None
        drid = int(drid) if drid else None
        chan = str(chan) if chan else None

        # if chan is given, then rebuild existing channels
        # note we overwrite input bid and drid if chan exists
        if chan:
            bid, drid, id, cid = _recoverChanParts(chan)

        # chan is not given, so generate new channels
        else:
            bid, drid, id, cid = _genChanParts(bid, drid)

        self.bid = bid
        self.drid = drid
        self.id = id
        self.cid = cid

        self.pub    = _pubChan(bid, drid, cid, ret=False)
        self.pubRet = _pubChan(bid, drid, cid, ret=True)
        self.sub    = _subChan(bid, drid, cid=None, ret=False)
        self.subRet = _subChan(bid, drid, cid=None, ret=True)


# ============================================================================ #
# subList
def subList(bid, drid):
    '''List of all channels to subscribe to for given bid and drid.

    bid: (int) Board identifier.
    drid: (int) Drone identifier {1,4}.
    '''

    chans = []
    chans += [_subChan(bid, drid, cid=None, ret=False)]
    chans += [_subChan(bid, drid=None, cid=None, ret=False)]
    chans += [_subChan(bid=None, drid=None, cid=None, ret=False)]
    
    chans = list(set(chans)) # remove repeats

    return chans




# ============================================================================ #
# Testing
# ============================================================================ #

def testBidDridChan():
    # bid, drid, chan
    bidDridChans = [
        (None, None, None),
        (1,    None, None), 
        (None, 1,    None), 
        (1,    1,    None)]
    
    for bidDridChan in bidDridChans:
        chan = comChan(*bidDridChan)
        print('='*20)
        print(f'{bidDridChan=}')
        print(f'{chan.bid=}')
        print(f'{chan.drid=}')
        print(f'{chan.id=}')
        print(f'{chan.cid=}')
        print(f'{chan.pub=}')
        print(f'{chan.pubRet=}')
        print(f'{chan.sub=}')
        print(f'{chan.subRet=}')

def testChan():
    # chan tests:
    chans = ['board', 'rets_board']
    chans += ['board_1', 'board_2', 'board_10', 'board_11', 'board_99', 'board_100', 'board_101']
    chans += ['board_1.1', 'board_1.2', 'board_1.3', 'board_1.4', 'board_1.5', 'board_1.10']
    chans += ['board_2.4', 'board_3.5', 'board_10.1', 'board_10.10']
    chans += ['board_16fd2706-8baf-433b-82eb-8c7fada847da', 'board_1_16fd2706-8baf-433b-82eb-8c7fada847da', 'board_1.1_16fd2706-8baf-433b-82eb-8c7fada847da']
    chans += ['rets_' + e for e in chans] # add rets version of all

    for chan in chans:
        cchan = comChan(None, None, chan)
        print('='*20)
        print(f'{chan=}')
        print(f'{cchan.bid=}')
        print(f'{cchan.drid=}')
        print(f'{cchan.id=}')
        print(f'{cchan.cid=}')
        print(f'{cchan.pub=}')
        print(f'{cchan.pubRet=}')
        print(f'{cchan.sub=}')
        print(f'{cchan.subRet=}')