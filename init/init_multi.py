from pynq import Overlay
import xrfclk
import xrfdc

import sys
import os

# Determine the directory where the script is located
script_dir = os.path.dirname(os.path.realpath(__file__))

# add src/ to path (where most of the other scripts live)
sys.path.insert(1, os.path.join(os.path.dirname(script_dir), 'src'))

import ip_addr
from config import board as cfg

import subprocess


try:

# ============================================================================ #
# Firmware, PTP, clocks

    # assuming cfg.firmware_file is a local filename
    firmware_file = os.path.join(cfg.dir_root, cfg.firmware_file)
    firmware = Overlay(firmware_file, ignore_version=True)

    clksrc = 409.6 # MHz
    xrfclk.set_all_ref_clks(clksrc)

    # Bring up the PTP interface
    subprocess.run(["ifconfig", cfg.ptp_interface, cfg.ptp_ip_address, "up"])

    # Pass the MAC address and interface to the PTP and PHC scripts
    run_ptp4l_path = os.path.join(script_dir, 'run_ptp4l.sh')
    subprocess.run([run_ptp4l_path, cfg.ptp_interface, cfg.ptp_mac_address])
    run_phc2sys_path = os.path.join(script_dir, 'run_phc2sys.sh')
    subprocess.run([run_phc2sys_path, cfg.ptp_interface])

    print("PTP configured")


# ============================================================================ #
# Digital Mixers

    lofreq = 1000.000 # [MHz]
    rf_data_conv = firmware.usp_rf_data_converter_0

    # chan: [adc tiles, adc blocks, dac tiles, dac blocks]
    name = os.path.splitext(os.path.basename(firmware_file))[0]
    if int(name[7:9]) >= 13:
        tb_indices = {
            1: [1,0,1,3], 2: [1,1,1,2], 3: [0,1,1,0], 4: [0,0,1,1]}
    else:
        tb_indices = {
            1: [0,0,1,3], 2: [0,1,1,2], 3: [1,0,1,1], 4: [1,1,1,0]}
    
    for chan, ii in tb_indices.items():
        adc = rf_data_conv.adc_tiles[ii[0]].blocks[ii[1]]
        dac = rf_data_conv.dac_tiles[ii[2]].blocks[ii[3]]

        adc.MixerSettings['Freq'] = lofreq
        dac.MixerSettings['Freq'] = lofreq
        adc.UpdateEvent(xrfdc.EVENT_MIXER)
        dac.UpdateEvent(xrfdc.EVENT_MIXER)



# ============================================================================ #
# Ethernet

    dest_ip = ip_addr.tIP_destination(sep='', asHex=True)
    dest_mac = ip_addr.mac_destination(sep='')
    src_ip_1 = ip_addr.tIP_origin(1, sep='', asHex=True)
    src_ip_2 = ip_addr.tIP_origin(2, sep='', asHex=True)
    src_ip_3 = ip_addr.tIP_origin(3, sep='', asHex=True)
    src_ip_4 = ip_addr.tIP_origin(4, sep='', asHex=True)
    src_mac = ip_addr.mac_origin(sep='')

    def ethRegsPortWrite(eth_regs, src_ip_int32): 
        eth_regs.write( 0x00, int(src_mac[4:], 16))
        eth_regs.write( 0x04, (int(dest_mac[-4:], 16)<<16) + int(src_mac[:4], 16))
        eth_regs.write( 0x08, int(dest_mac[:-4], 16))
        eth_regs.write( 0x0c, src_ip_int32)
        eth_regs.write( 0x10, int(dest_ip, 16))
    ethRegsPortWrite(firmware.ethWrapPort0.eth_regs_0, src_ip_int32=int(src_ip_1, 16))
    ethRegsPortWrite(firmware.ethWrapPort1.eth_regs_0, src_ip_int32=int(src_ip_2, 16))
    ethRegsPortWrite(firmware.ethWrapPort2.eth_regs_0, src_ip_int32=int(src_ip_3, 16))
    ethRegsPortWrite(firmware.ethWrapPort3.eth_regs_0, src_ip_int32=int(src_ip_4, 16))



except Exception as e:
    print(e)
