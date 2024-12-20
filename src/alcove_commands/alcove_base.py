
# ============================================================================ #
# alcove_base.py
# Alcove commands common base.
# James Burgoyne jburgoyne@phas.ubc.ca 
# CCAT Prime 2023  
# ============================================================================ #



# ============================================================================ #
# IMPORTS & GLOBALS
# ============================================================================ #

import os

import alcove_commands.board_io as io
import queen_commands.control_io as cio

try: from config import board as cfg_b
except ImportError: cfg_b = None 

try: import xrfdc # type: ignore
except ImportError: xrfdc = None

try: from pynq import Overlay # type: ignore
except ImportError: Overlay = None

# FIRMWARE UPLOAD
try:
    os.environ["TMPDIR"] = cfg_b.temp_dir

    with open(cfg_b.temp_dir+'/test.txt', "w") as f: f.write(cfg_b.temp_dir)

    firmware_file = os.path.join(cfg_b.dir_root, cfg_b.firmware_file)
    firmware = Overlay(firmware_file, ignore_version=True, download=False)
except Exception as e: 
    firmware = None


# import os
# from pynq import Overlay

# os.environ["TMPDIR"] = f"/tmp/drone_{os.getpid()}"
# firmware = Overlay(firmware_file, ignore_version=True, download=False)

    



# ============================================================================ #
# GENERAL FUNCTIONS
# ============================================================================ #


# ============================================================================ #
# freqOffsetFixHackFactor
# def freqOffsetFixHackFactor():
#     return 1.00009707 # need to check this


# ============================================================================ #
# safe_cast_to_int
def safe_cast_to_int(data_str):
    try:
        if data_str.lower().startswith('0x'):   # hex
            return int(data_str, 16)
        elif data_str.lower().startswith('0b'): # bin
            return int(data_str, 2)
        elif data_str.lower().startswith('0o'): # oct
            return int(data_str, 8)
        else:                                   # everything else
            return int(float(data_str)) # catches sci, underscores, etc.
    except (ValueError, SyntaxError) as e:
        # raise ValueError(f"Invalid integer string format: {data_str}") from e
        return None


# ============================================================================ #
# timestreamOn
def timestreamOn(on=True):
    '''Turn the UDP timestream on (or off) for the current drone.'''
    
    import time

    # input parameter casting
    on = str(on) in {True, 1, '1', 'True', 'true'}

    udp_control = firmware.gpio_udp_info_control
    
    # current drone channel
    chan = cfg_b.drid
    chan_bit = 1 << (chan - 1)  # in hex

    # chan dependent delay instead of resource locking
    delay_factor = 0.1 # in seconds
    time.sleep(chan*delay_factor - delay_factor)

    # get the current udp control state
    current_state = udp_control.read(0x00)

    # determine new state from channel, on/off status, and current state
    if on:
        new_state = current_state | chan_bit
    else:
        new_state = current_state & ~chan_bit

    # 0x00 offset 4 bit binary for UDP on/off lsb is chan 1 msb chan 4
    # e.g. udp_control.write(0x04, 1) turns on only chan 3
    udp_control.write(0x00, new_state)


# ============================================================================ #
# userPacket
def userPacket(data):
    '''Write 8 bit data into the UDP timestream packet.
    Each drone is given 8 bits of a 32 bit packet allocation.

    data: 8 bit int to write.
        Note that Redis will convert user input to string.
        e.g. 255 can be sent as:
            '255', '255.0', '0xFF', '0b11111111', '0o377'
        If conversion fails, then will write 0 instead.
    '''

    import time

    # input parameter casting
    data = safe_cast_to_int(data) # returns None if fails
    data = 0 if data is None else data # fails to 0
    data = data & 0xFF # ensure data is 8 bits

    udp_control = firmware.gpio_udp_info_control
    
    # current drone channel
    chan = cfg_b.drid

    # chan dependent delay instead of resource locking
    delay_factor = 0.1 # in seconds
    time.sleep(chan*delay_factor - delay_factor)

    # Calculate the shift amount based on the channel 
    # (chan 1 is the least significant byte)
    shift_amount = (chan - 1) * 8

    # get the current user data state
    current_state = udp_control.read(0x08)

    # determine the new state
    mask = 0xFF << shift_amount
    new_state = (current_state & ~mask) | (data << shift_amount)

    # Write the data
    udp_control.write(0x08, new_state)

# ============================================================================ #
# userPacketInfo 
def userPacketInfo(data):
    # 16 bit data
    # current drone channel
    chan = cfg_b.drid
    udp_control = firmware.gpio_udp_info_control
    we = 2**19
    info = 0*2**18
    #count = 1*2**18
    dronenum = (chan-1)*2**16 # drone number minus 1
    # setup value , info or count, and drone number
    udp_control.write(0x08, info + dronenum + data)
    # strobe write enable
    udp_control.write(0x08, we + info + dronenum + data)
    udp_control.write(0x08, info + dronenum + data)

# ============================================================================ #
# writeChannelCount 
def writeChannelCount(num_chans):
    # 16 bit value for number of active tones/channels in packet
    # current drone channel
    chan = cfg_b.drid
    udp_control = firmware.gpio_udp_info_control
    we = 2**19
    #info = 0*2**18
    count = 1*2**18
    dronenum = (chan-1)*2**16 # drone number minus 1
    # setup value , info or count, and drone number
    udp_control.write(0x08, count + dronenum + num_chans)
    # strobe write enable
    udp_control.write(0x08, we + count + dronenum + num_chans)
    udp_control.write(0x08, count + dronenum + num_chans)

# ============================================================================ #
# generateWaveDdr4
def generateWaveDdr4(freq_list, amp_list, phi):  

    import numpy as np

    # freq_list may be complex but imag parts should all be zero
    freq_list = np.real(freq_list)
    amp_list = np.real(amp_list)
    phi = np.real(phi)

    fs = cfg_b.wf_fs # 512e6 
    lut_len = cfg_b.wf_lut_len # 2**20
    fft_len = cfg_b.wf_fft_len # 1024
    k = np.int64(np.round(freq_list/(fs/lut_len)))
    freq_actual = k*(fs/lut_len)
    X = np.zeros(lut_len,dtype='complex')
    #phi = np.random.uniform(-np.pi, np.pi, np.size(freq_list))
    for i in range(np.size(k)):
        X[k[i]] = np.exp(-1j*phi[i])*amp_list[i] # multiply by amplitude
    x = np.fft.ifft(X) * lut_len
    bin_num = np.int64(np.round(freq_actual / (fs / fft_len)))
    f_beat = bin_num*fs/fft_len - freq_actual
    dphi0 = f_beat/(fs/fft_len)*2**16
    if np.size(dphi0) > 1:
        dphi = np.concatenate((dphi0, np.zeros(fft_len - np.size(dphi0))))
    else:
        z = np.zeros(fft_len)
        z[0] = dphi0
        dphi = z
    return x, dphi, freq_actual


# ============================================================================ #
# _getSnapData
# capture data from ADC
def _getSnapData(chan, mux_sel, wrap=False):

    import numpy as np
    from pynq import MMIO

    # WIDE BRAM
    if chan==1:
        axi_wide = firmware.chan1.axi_wide_ctrl# 0x0 max count, 0x8 capture rising edge trigger
        base_addr_wide = 0x00_A007_0000
    elif chan==2:
        axi_wide = firmware.chan2.axi_wide_ctrl
        base_addr_wide = 0x00_B000_0000
    elif chan==3:
        axi_wide = firmware.chan3.axi_wide_ctrl
        base_addr_wide = 0x00_B000_8000
    elif chan==4:
        axi_wide = firmware.chan4.axi_wide_ctrl
        base_addr_wide = 0x00_8200_0000
    else:
        return "Does not compute"
    max_count = 32768
    axi_wide.write(0x08, mux_sel<<1) # mux select 0-adc, 1-pfb, 2-ddc, 3-accum
    axi_wide.write(0x00, max_count - 16) # -4 to account for extra delay in write counter state machine
    axi_wide.write(0x08, mux_sel<<1 | 0)
    axi_wide.write(0x08, mux_sel<<1 | 1)
    axi_wide.write(0x08, mux_sel<<1 | 0)
    mmio_wide_bram = MMIO(base_addr_wide,max_count)
    wide_data = mmio_wide_bram.array[0:8192]# max/4, bram depth*word_bits/32bits
    if mux_sel==0:
        #adc parsing
        up0, lw0 = np.int16(wide_data[0::4] >> 16), np.int16(wide_data[0::4] & 0x0000ffff)
        up1, lw1 = np.int16(wide_data[1::4] >> 16), np.int16(wide_data[1::4] & 0x0000ffff)
        I = np.zeros(4096)
        Q = np.zeros(4096)
        Q[0::2] = lw0
        Q[1::2] = up0
        I[0::2] = lw1
        I[1::2] = up1
    elif mux_sel==1:
        # pfb
        chunk0 = (np.uint64(wide_data[1::4]) << np.uint64(32)) + np.uint64(wide_data[0::4])
        chunk1 = (np.uint64(wide_data[2::4]) << np.uint64(32)) + np.uint64(wide_data[1::4])
        q0 = np.int64((chunk0 & 0x000000000003ffff)<<np.uint64(46))/2**32
        i0 = np.int64(((chunk0>>18) & 0x000000000003ffff)<<np.uint64(46))/2**32
        q1 = np.int64(((chunk1>>4)  & 0x000000000003ffff)<<np.uint64(46))/2**32
        i1 = np.int64(((chunk1>>22)  & 0x000000000003ffff)<<np.uint64(46))/2**32
        I = np.zeros(4096)
        Q = np.zeros(4096)
        Q[0::2] = q0/2**14
        Q[1::2] = q1/2**14
        I[0::2] = i0/2**14
        I[1::2] = i1/2**14
    elif mux_sel==2:
        # ddc
        chunk0 = (np.uint64(wide_data[1::4]) << np.uint64(32)) + np.uint64(wide_data[0::4])
        chunk1 = (np.uint64(wide_data[2::4]) << np.uint64(32)) + np.uint64(wide_data[1::4])
        q0 = np.int64((chunk0 & 0x00000000000fffff)<<np.uint64(45))/2**32
        i0 = np.int64(((chunk0>>19) & 0x00000000000fffff)<<np.uint64(45))/2**32
        q1 = np.int64(((chunk1>>6)  & 0x00000000000fffff)<<np.uint64(45))/2**32
        i1 = np.int64(((chunk1>>25)  & 0x00000000000fffff)<<np.uint64(45))/2**32
        I = np.zeros(4096)
        Q = np.zeros(4096)
        Q[0::2] = q0/2**13
        Q[1::2] = q1/2**13
        I[0::2] = i0/2**13
        I[1::2] = i1/2**13
    elif mux_sel==3:
        # accum
        q0 = (np.int32(wide_data[1::4])).astype("float")
        i0 = (np.int32(wide_data[0::4])).astype("float")
        q1 = (np.int32(wide_data[3::4])).astype("float")
        i1 = (np.int32(wide_data[2::4])).astype("float")
        I = np.zeros(4096)
        Q = np.zeros(4096)
        Q[0::2] = q0
        Q[1::2] = q1
        I[0::2] = i0
        I[1::2] = i1
        I, Q = I[4:], Q[4:]

    if wrap:
        return io.returnWrapper(io.file.IQ_generic, (I,Q))
    else:
        return I, Q


# ============================================================================ #
# getSnapData
def getSnapData(mux_sel, wrap=True):
    chan = cfg_b.drid
    return _getSnapData(chan, int(mux_sel), wrap=wrap)


# ============================================================================ #
# getADCrms
def getADCrms():
    import numpy as np
    chan = cfg_b.drid
    I, Q = _getSnapData(chan,0,wrap=False)
    z = I + 1j*Q
    rms = np.sqrt(np.mean(z*np.conj(z)))
    print("RMS: ",rms)
    return


# ============================================================================ #
# _setNCLO
def _setNCLO(chan, lofreq):

    # lofreq *= freqOffsetFixHackFactor() # Fequency offset fix
    # implemented in tones._writeComb and alcove_base._setNCLO

    # import xrfdc
    rf_data_conv = firmware.usp_rf_data_converter_0
    name = os.path.splitext(os.path.basename(cfg_b.firmware_file))[0]
    if int(name[7:9]) >= 13:
        tb_indices = {
            1: [1,0,1,3], 2: [1,1,1,2], 3: [0,1,1,0], 4: [0,0,1,1]}
    else:
        tb_indices = {
            1: [0,0,1,3], 2: [0,1,1,2], 3: [1,0,1,1], 4: [1,1,1,0]}

    ii = tb_indices[chan]
    adc = rf_data_conv.adc_tiles[ii[0]].blocks[ii[1]]
    dac = rf_data_conv.dac_tiles[ii[2]].blocks[ii[3]]

    adc.MixerSettings['Freq'] = lofreq
    dac.MixerSettings['Freq'] = lofreq
    adc.UpdateEvent(xrfdc.EVENT_MIXER)
    dac.UpdateEvent(xrfdc.EVENT_MIXER)

def _getNCLO(chan):

    rf_data_conv = firmware.usp_rf_data_converter_0

    # adc tiles; adc blocks; dac tiles; dac blocks
    if chan == 1: 
        i = [0,0,1,3]
    elif chan == 2:
        i = [0,1,1,2]
    elif chan == 3:
        i = [1,0,1,1]
    elif chan == 4:
        i = [1,1,1,0]
    else:
        print("_getNCLO: Invalid chan!")
        return

    adc = rf_data_conv.adc_tiles[i[0]].blocks[i[1]]
    dac = rf_data_conv.dac_tiles[i[2]].blocks[i[3]]

    f_lo = adc.MixerSettings['Freq']

    return f_lo


# ============================================================================ #
# setNCLO
def setNCLO(f_lo):
    """
    setNCLO: set the numerically controlled local oscillator
           
    f_lo: center frequency in [MHz]
    """

    import numpy as np

    chan = cfg_b.drid
    f_lo = int(f_lo)
    _setNCLO(chan, f_lo)
    io.save(io.file.f_center_vna, f_lo*1e6)


# ============================================================================ #
# getNCLO
def getNCLO(chan=None):
    """Get the numerically controlled local oscillator value from register.
    """

    import numpy as np

    if chan is None:
        chan = cfg_b.drid

    f_lo = float(_getNCLO(chan))

    return f_lo


# ============================================================================ #
# _setNCLO2
def _setNCLO2(chan, lofreq):
    import numpy as np
    mix = firmware.mix_freq_set_0
    if chan == 1:
        offset = 0
    elif chan == 2:
        offset = 4
    elif chan == 3:
        offset = 8
    elif chan == 4:
        offset = 12
    else:
        return "Does not compute"
    # set fabric nclo frequency 
    # only for small frequency sweeps
    # 0x00 -  frequency[21 downto 0] 
    def nclo_num(freqMHz):
        # freq in MHz
        # returns 32 bit signed integer for setting nclo2
        # MHz_per_int = 512.0/2**22 #MHz per_step !check with spec-analyzer
        MHz_per_int = cfg_b.wf_fs/1e6/2**22
        digi_val = int(np.round(freqMHz/MHz_per_int))
        actual_freq = digi_val*MHz_per_int
        return digi_val, actual_freq

    digi_val, actual_freq = nclo_num(lofreq)
    mix.write(offset, digi_val) # frequency
    return

# ============================================================================ #
# _setAtten
def _setAtten(chan,direction,attenuation):

    from alcove_commands.transceiver_serialdriver import Transceiver
    
    #casting 
    chan = int(chan)
    attenuation = float(attenuation)

    atten = Transceiver("/dev/ttyACM0")
    if direction=="drive":
        d = 0 
    elif direction=="sense":
        d = 4
    else:
        print("Error: unrecognized direction string, needs to be drive or sense")
    atten_id = (chan-1) + d
    print(atten_id)
    atten.set_atten(atten_id, attenuation)

# ============================================================================ #
# setFineNCLO 
def setFineNCLO(df_lo):
    """
    setFineNCLO: set the fine frequency numerically controlled local oscillator
           
    df_lo: Center frequency shift, in [MHz].
    """

    # import numpy as np

    chan = cfg_b.drid
    df_lo = float(df_lo)
    return _setNCLO2(chan, df_lo)
    # TODO: modify f_center to reflect this fine adjustment
    # io.save(io.file.f_center_vna, f_lo*1e6)



# ============================================================================ #
# createCustomCombFiles
def createCustomCombFiles(freqs_rf=None, amps=None, phis=None):
    """Create custom comb files from arrays.
    Used in tones.writeTargCombFromCustomList().
    """

    if freqs_rf is not None:    io.save(io.file.f_rf_tones_comb_cust, freqs_rf)
    if amps is not None:        io.save(io.file.a_tones_comb_cust, amps)
    if phis is not None:        io.save(io.file.p_tones_comb_cust, phis)


# ============================================================================ #
# createCustomCombFilesFromCurrentComb
def createCustomCombFilesFromCurrentComb():
    """Create custom comb files from the current comb.
    """

    f_comb = io.load(io.file.f_rf_tones_comb)
    a_comb = io.load(io.file.a_tones_comb)
    p_comb = io.load(io.file.p_tones_comb)

    createCustomCombFiles(freqs_rf=f_comb, amps=a_comb, phis=p_comb)


# ============================================================================ #
# loadCustomCombFiles
def loadCustomCombFiles():
    """Load custom comb files into arrays.
    Used in tones.writeTargCombFromCustomList().
    """
    
    freqs_rf = io.load(io.file.f_rf_tones_comb_cust)
    amps     = io.load(io.file.a_tones_comb_cust)
    phis     = io.load(io.file.p_tones_comb_cust)

    return freqs_rf, amps, phis


# ============================================================================ #
# modifyCustomCombAmps
def modifyCustomCombAmps(factor=1):
    """Modify custom tone amps file by multiplying by given factor.
    """
    
    amps     = io.load(io.file.a_tones_comb_cust)
    amps *= float(factor)
    io.save(io.file.a_tones_comb_cust, amps)

# ============================================================================ #
# setAttenuator
def setAtten(direction, atten):
    """
    Set RF attenuator values on Arduino controlled RF gain board 
    direction - string "sense" or "drive"
    atten - float attenuation value in dB min 0 max 31.75
    """
    chan = cfg_b.drid
    atten = float(atten)
    direction = str(direction)
    return _setAtten(chan,direction,atten)
