# ============================================================================ #
# queen_agent.py
# OCS agent to control computer (queen) commands.
#
# James Burgoyne jburgoyne@phas.ubc.ca 
# CCAT Prime 2024
# ============================================================================ #

from ocs import ocs_agent, site_config
# from twisted.internet.defer import Deferred, inlineCallbacks

import queen
import alcove
import drone_control




# ======================================================================== #
# main
def main(args=None):
    args = site_config.parse_args(agent_class='ReadoutAgent', args=args)
    agent, runner = ocs_agent.init_site_agent(args)
    readout = ReadoutAgent(agent)

    # convenience function wrapping register_task
    def rt(s, f, b=True):
        return agent.register_task(s, f, blocking=b)

    # queen commands
    rt('getKeyValue', readout.getKeyValue)
    rt('setKeyValue', readout.setKeyValue)
    rt('getClientList', readout.getClientList)
    rt('getClientListLight', readout.getClientListLight)
    rt('action', readout.action)

    # drone commands
    rt('setNCLO', readout.setNCLO)
    rt('setFineNCLO', readout.setFineNCLO)
    rt('getSnapData', readout.getSnapData)
    rt('getADCrms', readout.getADCrms)
    rt('writeTestTone', readout.writeTestTone)
    rt('writeNewVnaComb', readout.writeNewVnaComb)
    rt('writeTargCombFromVnaSweep', readout.writeTargCombFromVnaSweep)
    rt('writeTargCombFromTargSweep', readout.writeTargCombFromTargSweep)
    rt('writeCombFromCustomList', readout.writeCombFromCustomList)
    rt('createCustomCombFilesFromCurrentComb', 
       readout.createCustomCombFilesFromCurrentComb)
    rt('modifyCustomCombAmps', readout.modifyCustomCombAmps)
    rt('writeTargCombFromCustomList', readout.writeTargCombFromCustomList)
    rt('vnaSweep', readout.vnaSweep)
    rt('targetSweep', readout.targetSweep)
    rt('customSweep', readout.customSweep)
    rt('findVnaResonators', readout.findVnaResonators)
    rt('findTargResonators', readout.findTargResonators)
    rt('findCalTones', readout.findCalTones)
    rt('sys_info', readout.sys_info)
    rt('sys_info_v', readout.sys_info_v)
    rt('timestreamOn', readout.timestreamOn)
    rt('userPacketInfo', readout.userPacketInfo)
    rt('setAtten', readout.setAtten)

    runner.run(agent, auto_reconnect=True)




# ============================================================================ #
# CLASS: ReadoutAgent
# ============================================================================ #
class ReadoutAgent:
    """Readout agent interfacing with queen.

    Parameters:
        agent (OCSAgent): OCSAgent object from :func:`ocs.ocs_agent.init_site_agent`.

    Attributes:
        
    """

    def __init__(self, agent):
        self.agent = agent


    # ======================================================================== #
    # getKeyValue
    @ocs_agent.param('key', type=str)
    def getKeyValue(self, session, params):
        """getKeyValue()

        **Task** - Return the value for the given key.

        Args
        -------
        key: str
            The key to fetch the value for.
        """
        
        return True, f"{params['key']}: {queen.getKeyValue(params['key'])}"


    # ======================================================================== #
    # setKeyValue
    @ocs_agent.param('key', type=str)
    @ocs_agent.param('value', type=str)
    def setKeyValue(self, session, params):
        """getKeyValue()

        **Task** - Set given key to given value.

        Args
        -------
        key: str
            The key to set.
        value: str
            The value to set for key.
        """
        
        return True, f"{params['key']}: {queen.setKeyValue(params['key'], params['value'])}"


    # ======================================================================== #
    # .getClientList
    def getClientList(self, session, params):
        """getClientList()

        **Task** - Return the list of Redis clients, verbose.
        """

        return True, f"client list: {queen.getClientList()}"
    
    
    # ======================================================================== #
    # .getClientListLight
    def getClientListLight(self, session, params):
        """getClientListLight()

        **Task** - Return the list of Redis clients.
        """

        return True, f"client list: {queen.getClientListLight()}"


    # ======================================================================== #
    # .action
    @ocs_agent.param('com_to', default=None, type=str)
    @ocs_agent.param('action', type=str)
    def action(self, session, params):
        """action()

        **Task** - Perform the drone control action, e.g. 'start'.

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
        action: str
            Drone control action to perform:
            'start', 'stop', 'restart', 'status', 
            'startAllDrones', 'stopAllDrones', 'restartAllDrones'
        """

        action = params['action']
        bid, drid = drone_control._bid_drid(params['com_to'])

        return True, f"action: {drone_control.action(action, bid, drid)}"


    # ======================================================================== #
    # .setNCLO
    @ocs_agent.param('com_to', default=None, type=str)
    @ocs_agent.param('f_lo', type=int)
    def setNCLO(self, session, params):
        """setNCLO()

        **Task** - Set the numerically controlled local oscillator.

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
            If None, will send to all drones.
            Default is None.
        f_lo: int
            Center frequency in [MHz].
        """
  
        rtn = _sendAlcoveCommand(
            com_str  = 'setNCLO', 
            com_to   = params['com_to'], 
            com_args = f'f_lo={params["f_lo"]}')
        
        # return is a fail message str or number of clients int
        return True, f"setNCLO: {rtn}"
    

    # ======================================================================== #
    # .setFineNCLO
    @ocs_agent.param('com_to', default=None, type=str)
    @ocs_agent.param('df_lo', type=float)
    def setFineNCLO(self, session, params):
        """setFineNCLO()

        **Task** - Set the fine frequency shift in the local oscillator.

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
            If None, will send to all drones.
            Default is None.
        df_lo: float
            Center frequency shift, in [MHz].
        """
  
        rtn = _sendAlcoveCommand(
            com_str  = 'setFineNCLO', 
            com_to   = params['com_to'], 
            com_args = f'f_lo={params["df_lo"]}')
        
        # return is a fail message str or number of clients int
        return True, f"setFineNCLO: {rtn}"


    # ======================================================================== #
    # .getSnapData
    @ocs_agent.param('com_to', default=None, type=str)
    @ocs_agent.param('mux_sel', type=int)
    def getSnapData(self, session, params):
        """getSnapData()

        **Task** - ?

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
            If None, will send to all drones.
            Default is None.
        mux_sel: float
            ?
        """
  
        rtn = _sendAlcoveCommand(
            com_str  = 'getSnapData', 
            com_to   = params['com_to'], 
            com_args = f'mux_sel={params["mux_sel"]}')
        
        # return is a fail message str or number of clients int
        return True, f"getSnapData: {rtn}"
    
    
    # ======================================================================== #
    # .getADCrms
    @ocs_agent.param('com_to', default=None, type=str)
    def getADCrms(self, session, params):
        """getADCrms()

        **Task** - Return the ADC RMS.
        """

        rtn = _sendAlcoveCommand(
            com_str  = 'getADCrms', 
            com_to   = params['com_to'])
        
        # return is a fail message str or number of clients int
        return True, f"getADCrms: {rtn}"
    

    # ======================================================================== #
    # .writeTestTone
    @ocs_agent.param('com_to', default=None, type=str)
    def writeTestTone(self, session, params):
        """writeTestTone()

        **Task** - Write a single test tone at 50 MHz.

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
            If None, will send to all drones.
            Default is None.
        """
  
        rtn = _sendAlcoveCommand(
            com_str  = 'writeTestTone', 
            com_to   = params['com_to'])
        
        # return is a fail message str or number of clients int
        return True, f"writeTestTone: {rtn}"


    # ======================================================================== #
    # .writeNewVnaComb
    @ocs_agent.param('com_to', default=None, type=str)
    def writeNewVnaComb(self, session, params):
        """writeNewVnaComb()

        **Task** - Create and write the vna sweep tone comb.

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
            If None, will send to all drones.
            Default is None.
        """
  
        rtn = _sendAlcoveCommand(
            com_str  = 'writeNewVnaComb', 
            com_to   = params['com_to'])
        
        # return is a fail message str or number of clients int
        return True, f"writeNewVnaComb: {rtn}"


    # ======================================================================== #
    # .writeTargCombFromVnaSweep
    @ocs_agent.param('com_to', default=None, type=str)
    @ocs_agent.param('cal_tones', default=False, type=bool)
    def writeTargCombFromVnaSweep(self, session, params):
        """writeTargCombFromVnaSweep()

        **Task** - Write the target comb from the vna sweep resonator frequencies. Note that vnaSweep and findVnaResonators must be run first.

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
            If None, will send to all drones.
            Default is None.
        cal_tones: bool
            Include calibration tones (True) or not (False).
            Note that findCalTones must be run first.
        """
  
        rtn = _sendAlcoveCommand(
            com_str  = 'writeTargCombFromVnaSweep', 
            com_to   = params['com_to'],
            com_args = f'cal_tones={params["cal_tones"]}')
        
        # return is a fail message str or number of clients int
        return True, f"writeTargCombFromVnaSweep: {rtn}"
    

    # ======================================================================== #
    # .writeTargCombFromTargSweep
    @ocs_agent.param('com_to', default=None, type=str)
    @ocs_agent.param('cal_tones', default=False, type=bool)
    @ocs_agent.param('new_amps_and_phis', default=False, type=bool)
    def writeTargCombFromTargSweep(self, session, params):
        """writeTargCombFromTargSweep()

        **Task** - Write the target comb from the target sweep resonator frequencies.
    Note that targSweep and findTargResonators must be run first.

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
            If None, will send to all drones.
            Default is None.
        cal_tones: bool
            Include calibration tones (True) or not (False).
            Note that findCalTones must be run first.
        new_amps_and_phis: bool 
            Generate new amplitudes and phases if True.
        """
  
        rtn = _sendAlcoveCommand(
            com_str  = 'writeTargCombFromTargSweep', 
            com_to   = params['com_to'],
            com_args = f'cal_tones={params["cal_tones"]}, new_amps_and_phis={params["cal_tones"]}')
        
        # return is a fail message str or number of clients int
        return True, f"writeTargCombFromTargSweep: {rtn}"


    # ======================================================================== #
    # .writeCombFromCustomList
    @ocs_agent.param('com_to', default=None, type=str)
    def writeCombFromCustomList(self, session, params):
        """writeCombFromCustomList()

        **Task** - Write the comb from custom tone files:
            alcove_commands/custom_freqs.npy
            alcove_commands/custom_amps.npy
            alcove_commands/custom_phis.npy

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
            If None, will send to all drones.
            Default is None.
        """
  
        rtn = _sendAlcoveCommand(
            com_str  = 'writeCombFromCustomList', 
            com_to   = params['com_to'])
        
        # return is a fail message str or number of clients int
        return True, f"writeCombFromCustomList: {rtn}"


    # ======================================================================== #
    # .createCustomCombFilesFromCurrentComb
    @ocs_agent.param('com_to', default=None, type=str)
    def createCustomCombFilesFromCurrentComb(self, session, params):
        """createCustomCombFilesFromCurrentComb()

        **Task** - Create custom comb files from the current comb.

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
            If None, will send to all drones.
            Default is None.
        """
  
        rtn = _sendAlcoveCommand(
            com_str  = 'createCustomCombFilesFromCurrentComb', 
            com_to   = params['com_to'])
        
        # return is a fail message str or number of clients int
        return True, f"createCustomCombFilesFromCurrentComb: {rtn}"


    # ======================================================================== #
    # .modifyCustomCombAmps
    @ocs_agent.param('com_to', default=None, type=str)
    @ocs_agent.param('factor', default=1, type=float)
    def modifyCustomCombAmps(self, session, params):
        """modifyCustomCombAmps()

        **Task** - Modify custom tone amps file by multiplying by given factor.

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
            If None, will send to all drones.
            Default is None.
        factor: float
            Factor to multiply tone amps by.
        """
  
        rtn = _sendAlcoveCommand(
            com_str  = 'modifyCustomCombAmps', 
            com_to   = params['com_to'],
            com_args = f'factor={params["factor"]}')
        
        # return is a fail message str or number of clients int
        return True, f"modifyCustomCombAmps: {rtn}"


    # ======================================================================== #
    # .writeTargCombFromCustomList
    @ocs_agent.param('com_to', default=None, type=str)
    def writeTargCombFromCustomList(self, session, params):
        """writeTargCombFromCustomList()

        **Task** - Write the target comb from custom tone files:
            alcove_commands/custom_freqs.npy
            alcove_commands/custom_amps.npy
            alcove_commands/custom_phis.npy

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
            If None, will send to all drones.
            Default is None.
        """
  
        rtn = _sendAlcoveCommand(
            com_str  = 'writeTargCombFromCustomList', 
            com_to   = params['com_to'])
        
        # return is a fail message str or number of clients int
        return True, f"writeTargCombFromCustomList: {rtn}"


    # ======================================================================== #
    # .vnaSweep
    @ocs_agent.param('com_to', default=None, type=str)
    def vnaSweep(self, session, params):
        """vnaSweep()

        **Task** - Perform a stepped frequency sweep with current comb, save as vna sweep.

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
            If None, will send to all drones.
            Default is None.
        """
  
        rtn = _sendAlcoveCommand(
            com_str  = 'vnaSweep', 
            com_to   = params['com_to'])
        
        # return is a fail message str or number of clients int
        return True, f"vnaSweep: {rtn}"
    

    # ======================================================================== #
    # .targetSweep
    @ocs_agent.param('com_to', default=None, type=str)
    def targetSweep(self, session, params):
        """targetSweep()

        **Task** - Perform a sweep with current comb, save as target sweep.

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
            If None, will send to all drones.
            Default is None.
        """
  
        rtn = _sendAlcoveCommand(
            com_str  = 'targetSweep', 
            com_to   = params['com_to'])
        
        # return is a fail message str or number of clients int
        return True, f"targetSweep: {rtn}"


    # ======================================================================== #
    # .customSweep
    @ocs_agent.param('com_to', default=None, type=str)
    @ocs_agent.param('bw', default=None, type=float)
    def customSweep(self, session, params):
        """customSweep()

        **Task** - Perform a sweep with current (custom) comb.

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
            If None, will send to all drones.
            Default is None.
        bw: float
            Channel bandwidth.
        """
    
        if params["bw"]:
            rtn = _sendAlcoveCommand(
                com_str  = 'customSweep', 
                com_to   = params['com_to'],
                com_args = f'bw={params["bw"]}')
        else: # allow func bw default
            rtn = _sendAlcoveCommand(
                com_str  = 'customSweep', 
                com_to   = params['com_to'])
        
        # return is a fail message str or number of clients int
        return True, f"customSweep: {rtn}"


    # ======================================================================== #
    # .findVnaResonators
    @ocs_agent.param('com_to', default=None, type=str)
    @ocs_agent.param('peak_prom_std', default=10, type=float)
    @ocs_agent.param('peak_prom_db', default=0, type=float)
    @ocs_agent.param('peak_dis', default=100, type=int)
    @ocs_agent.param('width_min', default=5, type=int)
    @ocs_agent.param('width_max', default=100, type=int)
    @ocs_agent.param('stitch', default=True, type=bool)
    @ocs_agent.param('stitch_sw', default=100, type=int)
    @ocs_agent.param('remove_cont', default=True, type=bool)
    @ocs_agent.param('continuum_wn', default=300, type=int)
    @ocs_agent.param('remove_noise', default=True, type=bool)
    @ocs_agent.param('noise_wn', default=30_000, type=int)
    def findVnaResonators(self, session, params):
        """findVnaResonators()

        **Task** - Find the resonator peak frequencies from vnaSweep S21. 
        Note that vnaSweep must be run first.

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
            If None, will send to all drones.
            Default is None.
        peak_prom_std: (float) 
            Peak height from surroundings, in noise std multiples.
            Uses larger of peak_prom_db or peak_prom_std.
        peak_prom_db: (float)
            Peak height from surroundings, in Db.
            Uses larger of peak_prom_db or peak_prom_std.
        peak_dis: (int) 
            Min distance between peaks [bins].
        width_min: (int) 
            Peak width minimum. [bins]
        width_max: (int) 
            Peak width maximum. [bins]
        stitch: (bool) 
            Whether to stitch (comb discontinuities).
        stitch_sw: (int) 
            Discontinuity edge size for alignment [bins].
        remove_cont: (bool) 
            Whether to subtract the continuum.
        continuum_wn: (int) 
            Continuum filter cutoff frequency [Hz].
        remove_noise: (bool) 
            Whether to subtract noise.
        noise_wn: (int) 
            Noise filter cutoff frequency [Hz].
        """
  
        com_args = ''
        com_args += f'peak_prom_std={params["stitch_bw"]}, '
        com_args += f'peak_prom_db={params["peak_prom_db"]}, '
        com_args += f'peak_dis={params["peak_dis"]}, '
        com_args += f'width_min={params["width_min"]}, '
        com_args += f'width_max={params["width_max"]}, '
        com_args += f'stitch={params["stitch"]}, '
        com_args += f'stitch_sw={params["stitch_sw"]}, '
        com_args += f'remove_cont={params["remove_cont"]}, '
        com_args += f'continuum_wn={params["continuum_wn"]}, '
        com_args += f'remove_noise={params["remove_noise"]}, '
        com_args += f'noise_wn={params["noise_wn"]}'

        rtn = _sendAlcoveCommand(
            com_str  = 'findVnaResonators', 
            com_to   = params['com_to'],
            com_args = com_args)
        
        # return is a fail message str or number of clients int
        return True, f"findVnaResonators: {rtn}"


    # ======================================================================== #
    # .findTargResonators
    @ocs_agent.param('com_to', default=None, type=str)
    @ocs_agent.param('stitch_bw', default=500, type=int)
    def findTargResonators(self, session, params):
        """findTargResonators()

        **Task** - Find the resonator peak frequencies from targSweep S21.
            See findResonators() for possible arguments.
            Note that targSweep must be run first.

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
            If None, will send to all drones.
            Default is None.
        stitch_bw: int 
            Width of the stitch bins.
        """
  
        rtn = _sendAlcoveCommand(
            com_str  = 'findTargResonators', 
            com_to   = params['com_to'],
            com_args = f'stitch_bw={params["stitch_bw"]}')
        
        # return is a fail message str or number of clients int
        return True, f"findTargResonators: {rtn}"


    # ======================================================================== #
    # .findCalTones
    @ocs_agent.param('com_to', default=None, type=str)
    @ocs_agent.param('f_lo', default=0.1, type=float)
    @ocs_agent.param('f_hi', default=50, type=float)
    @ocs_agent.param('tol', default=2, type=float)
    @ocs_agent.param('max_tones', default=10, type=int)
    def findCalTones(self, session, params):
        """findCalTones()

        **Task** - Determine the indices of calibration tones.

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
            If None, will send to all drones.
            Default is None.
        f_hi: float 
            Highpass filter cutoff frequency (data units).
        f_lo: float 
            lowpass filter cutoff frequency (data units).
        tol: float 
            Reject tones tol*std_noise from continuum.
        max_tones: int 
            Maximum number of tones to return.
        """
  
        rtn = _sendAlcoveCommand(
            com_str  = 'findCalTones', 
            com_to   = params['com_to'],
            com_args = f'f_hi={params["f_hi"]}, f_lo={params["f_lo"]}, tol={params["tol"]}, max_tones={params["max_tones"]}')
        
        # return is a fail message str or number of clients int
        return True, f"findCalTones: {rtn}"


    # ======================================================================== #
    # .sys_info
    @ocs_agent.param('com_to', default=None, type=str)
    def sys_info(self, session, params):
        """sys_info()

        **Task** - Get system info from board.

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
            If None, will send to all drones.
            Default is None.
        """
  
        rtn = _sendAlcoveCommand(
            com_str  = 'sys_info', 
            com_to   = params['com_to'])
        
        # return is a fail message str or number of clients int
        return True, f"sys_info: {rtn}"
    

    # ======================================================================== #
    # .sys_info_v
    @ocs_agent.param('com_to', default=None, type=str)
    def sys_info_v(self, session, params):
        """sys_info_v()

        **Task** - Get system info from board, verbose.

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
            If None, will send to all drones.
            Default is None.
        """
  
        rtn = _sendAlcoveCommand(
            com_str  = 'sys_info_v', 
            com_to   = params['com_to'])
        
        # return is a fail message str or number of clients int
        return True, f"sys_info_v: {rtn}"


    # ======================================================================== #
    # .timestreamOn
    @ocs_agent.param('com_to', default=None, type=str)
    @ocs_agent.param('on', default=True, type=bool)
    def timestreamOn(self, session, params):
        """timestreamOn()

        **Task** - Turn the boards date timestream on/off.

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
            If None, will send to all drones.
            Default is None.
        on: bool
            Timestream on/off.
        """
  
        rtn = _sendAlcoveCommand(
            com_str  = 'timestreamOn', 
            com_to   = params['com_to'],
            com_args = f"on={params['on']},")
        
        # return is a fail message str or number of clients int
        return True, f"timestreamOn: {rtn}"
    

    # ======================================================================== #
    # .userPacketInfo
    @ocs_agent.param('com_to', default=None, type=str)
    @ocs_agent.param('data', type=int)
    def userPacketInfo(self, session, params):
        """userPacketInfo()

        **Task** - Write given data to timestream packet.

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
            If None, will send to all drones.
            Default is None.
        data: 16 bit int
            Data to write to packet.
        """
  
        rtn = _sendAlcoveCommand(
            com_str  = 'userPacketInfo', 
            com_to   = params['com_to'],
            com_args = f"data={params['data']}")
        
        # return is a fail message str or number of clients int
        return True, f"userPacketInfo: {rtn}"


    # ======================================================================== #
    # .setAtten
    @ocs_agent.param('com_to', default=None, type=str)
    @ocs_agent.param('direction', type=str)
    @ocs_agent.param('atten', type=float)
    def setAtten(self, session, params):
        """setAtten()

        **Task** - Set attenuator value on drive/sense gain board.

        Args
        -------
        com_to: str
            Drone to send command to in format bid.drid.
            If None, will send to all drones.
            Default is None.
        direction: (str)
            "sense" or "drive"
        atten: (float)
            Attenuation value in dB min 0 max 31.75
        """
  
        direction = params['direction']
        atten = params['atten']

        rtn = _sendAlcoveCommand(
            com_str  = 'setAtten', 
            com_to   = params['com_to'],
            com_args = f'direction={direction}, atten={atten},')
        
        # return is a fail message str or number of clients int
        return True, f"setAtten: {rtn}"
    



# ============================================================================ #
# INTERNAL FUNCTIONS
# ============================================================================ #


# ============================================================================ #
# _comNumAlcove
def _comNumAlcove(com_str):

    print(f"_comNumAlcove... com_str={com_str}, keys:")
    print(alcove.comList())

    return alcove.comNumFromStr(com_str)
    # coms = {alcove.com[key].__name__:key for key in alcove.com.keys()}
    # return coms[com_str]


# ============================================================================ #
# _sendAlcoveCommand
def _sendAlcoveCommand(com_str, com_to, com_args=None):
    """Send Alcove command.

    com_str:    (str)   String name of command. 
                        See alcove.py::_com(). 
                        E.g. 'alcove_base.setNCLO'
    com_to:     (str)   Drone to send command to.
                        E.g. '1.1' is board 1, drone 1.
    com_args:   (str)   Command arguments.
                        E.g. 'f_lo=500'
    """

    print(com_str, com_to, com_args)

    com_num = _comNumAlcove(com_str)

    print(com_num)

    # specific board/drone command
    if com_to:
        ids = com_to.split('.')
        bid = int(ids[0]) # must exist
        drid = int(ids[1]) if len(ids)>1 else None
        if drid:
            return queen.alcoveCommand(com_num, bid=bid, drid=drid, args=com_args)
        else:
            return queen.alcoveCommand(com_num, bid=bid, args=com_args)

    # all-boards commands
    else:
        return queen.alcoveCommand(com_num, all_boards=True, args=com_args)
    



if __name__ == '__main__':
    main()
