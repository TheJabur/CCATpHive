# ============================================================================ #
# pcs_client_test.py
# Script to test the queen_agent.
#
# James Burgoyne jburgoyne@phas.ubc.ca 
# CCAT Prime 2023  
# ============================================================================ #

# import argparse
from ocs.ocs_client import OCSClient

# Setting up the queen agent
print("Connecting to queenagent...", end="")
queen_agent = OCSClient('queenagent', args=[])
print(" Done.")

def testFunc(func, msg1):
    print("")
    print(msg1, end="")
    rtn = func
    print(" Done.")
    print(rtn)

testFunc(queen_agent.getClientList(), "Getting queen client list...")
testFunc(queen_agent.setNCLO(com_to='1.1', f_lo=500), "Sending setNCLO command...")
testFunc(queen_agent.writeNewVnaComb(com_to='1.1'), "Sending writeNewVnaComb command...")
testFunc(queen_agent.vnaSweep(com_to='1.1'), "Sending vnaSweep command...")



# print("")
# print("Sending sys_info command...", end="")
# sys_info_msg = queen_agent.sys_info(com_to='1.1')
# print(" Done.")
# print(f"sys_info message: {sys_info_msg}")

# print("")
# print("Sending SILENT sys_info command...", end="")
# sys_info_msg = queen_agent.sys_info(com_to='1.1', silent=True)
# print(" Done.")
# print(f"sys_info message: {sys_info_msg}")

# print("Sending setFineNCLO command...", end="")
# msg = queen_agent.setFineNCLO(com_to='1.1', df_lo=1)
# print(" Done.")
# print(f"setFineNCLO message: {msg}")

# print("Sending getSnapData command...", end="")
# msg = queen_agent.getSnapData(com_to='1.1', mux_sel=0)
# print(" Done.")
# print(f"getSnapData message: {msg}")

# print("Sending writeTargCombFromVnaSweep command...", end="")
# msg = queen_agent.writeTargCombFromVnaSweep(com_to='1.1', cal_tones=False)
# print(" Done.")
# print(f"writeTargCombFromVnaSweep message: {msg}")

# print("Sending writeTargCombFromTargSweep command...", end="")
# msg = queen_agent.writeTargCombFromTargSweep(
#     com_to='1.1', cal_tones=False, new_amps_and_phis=False)
# print(" Done.")
# print(f"writeTargCombFromTargSweep message: {msg}")

# print("Sending writeCombFromCustomList command...", end="")
# msg = queen_agent.writeCombFromCustomList(com_to='1.1')
# print(" Done.")
# print(f"writeCombFromCustomList message: {msg}")

# print("Sending createCustomCombFilesFromCurrentComb command...", end="")
# msg = queen_agent.createCustomCombFilesFromCurrentComb(com_to='1.1')
# print(" Done.")
# print(f"createCustomCombFilesFromCurrentComb message: {msg}")

# print("Sending modifyCustomCombAmps command...", end="")
# msg = queen_agent.modifyCustomCombAmps(com_to='1.1', factor=1)
# print(" Done.")
# print(f"modifyCustomCombAmps message: {msg}")

# print("Sending targetSweep command...", end="")
# msg = queen_agent.targetSweep(com_to='1.1', N_steps=500, chan_bandwidth=0.2)
# print(" Done.")
# print(f"targetSweep message: {msg}")

# print("Sending findVnaResonators command...", end="")
# msg = queen_agent.findVnaResonators(com_to='1.1', stitch_bw=500, stitch_sw=100, f_hi=50, f_lo=1, prom_dB=1, distance=30, width_min=5, width_max=100)
# print(" Done.")
# print(f"findVnaResonators message: {msg}")

# print("Sending findTargResonators command...", end="")
# msg = queen_agent.findTargResonators(com_to='1.1', stitch_bw=500)
# print(" Done.")
# print(f"findTargResonators message: {msg}")

# print("Sending findCalTones command...", end="")
# msg = queen_agent.findCalTones(com_to='1.1', f_lo=0.1, f_hi=50, tol=2, max_tones=10)
# print(" Done.")
# print(f"findCalTones message: {msg}")


# Parser for collecting the necessary arguments
# Use: python3 pcs_client_test.py posArgValues -namedArgs namedArgValues
# parser = argparse.ArgumentParser()
# parser.add_argument("mode", help="Whether to turn the still heater on or off",
# 					type=str, choices=['on','off'])
# parser.add_argument("-p", "--power", help="The still heater power to set", type=float)
# args = parser.parse_args()
# # use: args.mode, args.power