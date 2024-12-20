# ============================================================================ #
# sys_info.py
# Script to produce system information dictionary.
# James Burgoyne jburgoyne@phas.ubc.ca
# CCAT/FYST 2024
# ============================================================================ #

import os
import subprocess
import numpy as np
from datetime import datetime, timezone

import alcove_commands.board_utilities as utils
import alcove_commands.board_io as io

try: from config import queen as cfg_q
except ImportError: cfg_q = None

try: from config import board as cfg_b
except ImportError: cfg_b = None  




# ============================================================================ #
# sys_info
def sys_info_v():
    '''Dictionary containing all system information.'''

    info_dicts = [
        _getDroneID(),               # board and drone ID, bid.drid
        _getTimestamp(),             # current timestamp, UTC
        _getConfigBoard(),           # config: board
        _getConfigQueen(),           # config: queen
        _getUptime(),                # system uptime
        _getVersPrimecam_readout(),  # primecam_readout version
        _getVersFirmwareRfsoc(),     # firmware version
        _getVersOs(),                # OS version
        _getVersRedis(),             # Redis version
        _getNetwork(),               # network connections info
        _getTemps(),                 # board temperature sensors
        # _getPtp(), # PTP info
        _getRecentAuthLogEvents(),   # recent auth log entries
        _getRecentSysLogEvents(),    # recent sys log entries
        _getRecentDmesgEvents(),     # recent dmesg entries
        _getVersApt(),               # apt list
        _getNetwork(),               # network connections info
    ]

    merged_dict = {}
    for d in info_dicts:
        merged_dict.update(d)

    return io.returnWrapper(io.file.sys_info_v, np.array(merged_dict))
    # return merged_dict


# ============================================================================ #
# sys_info
def sys_info():
    '''Dictionary containing all system information.'''

    info_dicts = [
        _getDroneID(),               # board and drone ID, bid.drid
        _getTimestamp(),             # current timestamp, UTC
        _getConfigBoard(),           # config: board
        _getConfigQueen(),           # config: queen
        _getUptime(),                # system uptime
        _getVersPrimecam_readout(),  # primecam_readout version
        _getVersFirmwareRfsoc(),     # firmware version
        _getTemps(),                 # board temperature sensors
        _getRecentAuthLogEvents(),   # recent auth log entries
        _getRecentSysLogEvents(),    # recent sys log entries
        _getRecentDmesgEvents(),     # recent dmesg entries
        _getNetwork(),               # network connections info
    ]

    merged_dict = {}
    for d in info_dicts:
        merged_dict.update(d)

    return io.returnWrapper(io.file.sys_info, np.array(merged_dict))
    # return merged_dict



# ============================================================================ #
# _getDroneInfo
def _getDroneID():
    '''Dictionary of board and drone identifier (bid.drid).'''

    return {'bid.drid': f"{cfg_b.bid}.{cfg_b.drid}"}


def _getTimestamp():
    '''Dictionary of current timestamp in UTC.'''

    t = datetime.now(timezone.utc)
    return {'timestamp_utc': t.timestamp() }


# ============================================================================ #
# _getUptime
def _getUptime():
    '''Dictionary of system uptime in seconds.'''

    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])

    return {'uptime_seconds':uptime_seconds}


# ============================================================================ #
# _getVersPrimecam_readout
def _getVersPrimecam_readout():
    '''Dictionary of version string for primecam_readout.'''

    file_path = f'../VERSION' # {parentDir()}
    with open(file_path, 'r') as version_file:
        version = version_file.read().strip()

    ## the current method requires a build action
    ## the following method does not
    ## however git is not a standard library
    ## and it would fail if the code is removed from git
    # import git
    # repo = git.Repo(search_parent_directories=True)
    # version = repo.head.commit.hexsha

    return {'version:primecam_readout':version}


# ============================================================================ #
# _getVersFirmwareRfsoc
def _getVersFirmwareRfsoc():
    '''Dictionary of version string for RFSoC firmware.
    Note that this depends on the bit file being the same version as flashed.'''

    filename = cfg_b.firmware_file # e.g. 'tetra_v7p1_impl_5.bit'
    # name = os.path.splitext(filename)[0]
    name = os.path.splitext(os.path.basename(filename))[0]

    return {'version:firmware_rfsoc':name}


# ============================================================================ #
# _getVersOs
def _getVersOs():
    '''Dictionary of OS version.'''

    os_version = {}
    with open('/etc/os-release', 'r') as f:
        for line in f:
            key, value = line.strip().split('=', 1)
            os_version[key] = value.strip('"')
    str = os_version.get('PRETTY_NAME', 'Unknown OS Version')

    return {'version:os':str}


# ============================================================================ #
# _getVersApt
def _getVersApt():
    '''Dictionary of apt software list and versions.'''

    result = subprocess.run(['apt', 'list', '--installed'], 
                            stdout=subprocess.PIPE, universal_newlines=True)
    packages = result.stdout.splitlines()

    software_list = {}
    for package in packages[1:]:  # Skip the first line as it is a header
        if package:
            parts = package.split('/')
            name = parts[0]
            version = parts[1].split()[1]
            software_list[name] = version

    return {'version:apt':software_list}


# ============================================================================ #
# _getConfigBoard
def _getConfigBoard():
    '''Dictionary of board config variables.'''

    attributes = dir(cfg_b)
    variables = {
        attr: getattr(cfg_b, attr) 
        for attr in attributes if not attr.startswith("__")
        }

    return {'config:board':variables}


# ============================================================================ #
# _getConfigQueen
def _getConfigQueen():
    '''Dictionary of queen config variables.'''

    attributes = dir(cfg_q)
    variables = {
        attr: getattr(cfg_q, attr) 
        for attr in attributes if not attr.startswith("__")
        }

    return {'config:queen':variables}


# ============================================================================ #
# _getRecentAuthLogEvents
def _getRecentAuthLogEvents(log_file_path='/var/log/auth.log', num_lines=10):
    '''Dictionary of recent auth log entries.'''

    with open(log_file_path, 'r') as file:
        lines = file.readlines() # Read all lines from the log file
        recent_lines = lines[-num_lines:] # Get the most recent 'num_lines' events
    
    return {'log:auth':recent_lines}


# ============================================================================ #
# _getRecentSysLogEvents
def _getRecentSysLogEvents(log_file_path='/var/log/syslog', num_lines=10):
    '''Dictionary of recent sys log entries.'''

    with open(log_file_path, 'r') as file:
        lines = file.readlines() # Read all lines from the log file
        # Get the most recent 'num_lines' events
        recent_lines = lines[-num_lines:]

    return {'log:sys':recent_lines}


# ============================================================================ #
# _getRecentDmesgEvents
def _getRecentDmesgEvents(num_lines=10):
    '''Dictionary of dmesg log entries.'''

    # Use subprocess to call the dmesg command and capture the output
    result = subprocess.run(['dmesg', '-T', '--level=err,warn'], stdout=subprocess.PIPE, universal_newlines=True)
    dmesg_output = result.stdout.splitlines()
    # Get the most recent 'num_lines' events
    recent_dmesg_lines = dmesg_output[-num_lines:]

    return {'log:dmesg':recent_dmesg_lines}


# ============================================================================ #
# _getNetwork
def _getNetwork():
    '''Dictionary of network info.'''
    
    result = subprocess.run(['ip', '-br', 'addr'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    return {'network':result.stdout}

    # Fallback to using `ifconfig` if `ip` is not available
    # result = subprocess.run(['ifconfig'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    # if result.returncode == 0:
    #     return result.stdout
    # else:
    #     raise Exception(result.stderr)



# ============================================================================ #
# _getVersRedis
def _getVersRedis():
    '''Dictionary of redis version.'''

    # Run the command to get the Redis server version
    result = subprocess.run(['redis-server', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    
    # Extract the version number from the output
    version_info = result.stdout.split()
    for item in version_info:
        if item.startswith("v="):
            vers = item.split('=')[1]
    
    return {'version:redis':vers}


# ============================================================================ #
# _getTemps
def _getTemps():
    '''Dictionary of board temperatures.'''

    try:
        return {'temps_board':utils.boardTemps()}
    except:
        return {}


# ============================================================================ #
# _getPtp
def _getPtp():
    pass