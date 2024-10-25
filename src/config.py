# ============================================================================ #
# config.py
# Script to manage configuration file imports.
# James Burgoyne jburgoyne@phas.ubc.ca
# CCAT Prime 2023   
# ============================================================================ #


import sys, os


def thisDir(file):
    '''Directort where given file is located.'''
    return os.path.dirname(os.path.abspath(file))
    # return os.path.dirname(os.path.realpath(file))


def parentDir(file):
    '''Parent directory of given file.'''
    return os.path.dirname(thisDir(file))


# define primecam_readout base dir
dir_root = parentDir(__file__)

# add parent dir to path
sys.path.insert(1, dir_root)

try:
    from cfg import _cfg_queen as queen
except ImportError:
    print("Error: _cfg_queen.py is missing from cfg/ directory.")
    raise

try:
    from cfg import _cfg_board as board
except ImportError:
    print("Error: _cfg_board.py is missing from cfg/ directory.")
    raise
