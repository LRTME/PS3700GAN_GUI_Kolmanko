import math
import socket_creation


class PPA5500:

    """
    NOTE: DEVICE CAN ONLY BE CONNECTED WITH USING IP!!! DEVICE IS NOT SHOWN IN RESOURCE LIST, THEREFORE NAME CANNOT
    BE USED!!
    DEVICE HAS TO BE USED USING SOCKET AND PORT (DEFAULT PORT = 10001) OR ELSE CONNECTION WILL NOT BE ESTABLISHED!
    """
    def __init__(self, ip_or_name, socket = True, port = 10001):
        self.addr = socket_creation.create_socket(ip_or_name, socket, port)

    def get_id(self):
        return self.addr.query("*IDN?")

    def start(self):
        """
        Initiates a new measurement, resets the range and smoothing.
        """
        self.addr.write("START")

    def stop(self):

        self.addr.write("STOP") # ABORT? SUSPEN?

    def trigger(self):
        self.addr.write("*TRG")

    def is_measurement_done(self):
        is_available = self.addr.query("DAV?")
        if is_available:
            return True
        else:
            return False

    def set_data_hold(self, hold = "OFF"):
        """
        Turns data hold on or off.
        Useful for reading data from different phases without it being changed between reads.
        can take values ON|OFF
        """
        assert hold in ["ON", "OFF"]
        self.addr.write("HOLD,{0}".format(hold))

    def set_operating_mode(self, mode = "POWER"):
        """
        Sets the basic operating mode of the instrument.
        can take values:
        POWER: power meter
        INTEGR: integrator
        HARMON: harmonic analyser
        RMS: rms voltmeter
        LCR: LCR meter
        SCOPE: oscilloscope
        PHASEM: phase meter
        """
        assert mode in ["POWER", "INTEGR", "HARMON", "RMS", "LCR", "SCOPE", "PHASEM"]
        self.addr.write("MODE,{0}".format(mode))

    def get_voltage(self, phase = 1):

        assert phase in [1, 2, 3, "S", "SUM", "NEUTRAL"]
        answer = self.addr.query("POWER,PHASE{0},VOLTAGE?".format(phase))
        split_data = answer.split(",")
        returned = split_data[2]
        return returned

    def get_current(self, phase = 1):
        assert phase in [1, 2, 3, "S", "SUM", "NEUTRAL"]

        answer = self.addr.query("POWER,PHASE{0},CURRENT?".format(phase))
        split_data = answer.split(",")
        returned = split_data[2]
        return returned

    def get_power(self, phase = 1):
        assert phase in [1, 2, 3, "S", "SUM", "NEUTRAL"]
        answer = self.addr.query("POWER,PHASE{0},WATTS?".format(phase))
        split_data = answer.split(",")
        returned = split_data[2]
        return returned

    def get_voltage_rms(self, phase = 1):
        assert phase in [1, 2, 3, "S", "SUM", "NEUTRAL"]
        answer = self.addr.query("VRMS,PHASE{0},RMS?".format(phase))
        split_data = answer.split(",")
        returned = split_data[phase]
        return returned

    def get_phase(self, phase = 1):
        """
        Reads phase meter results.
        Sets phase meter mode if not already set.
        Waits for next unread data if available.
        Clears new data available bit read by DAV?
        """
        assert phase in [1,2,3,"S"]
        answer = self.addr.query("PHASEM,PHASE{0}?".format(phase))
        split_data = answer.split(",")
        returned = split_data[5]
        return returned

    def get_power_factor(self, phase = 1):
        assert phase in [1, 2, 3, "S", "SUM", "NEUTRAL"]
        get_phase = self.get_phase(phase)
        return math.cos(get_phase)

    def set_shunt_mode_and_value(self, channel = 1, internal_or_external = "external", shunt_resistance = 0.001):
        """
        set the shunt mode to internal or external
        set the value of the external shunt for desired channel.
        Channels range from 1 to 3.
        Shunt resistance is set in ohms.
        NOTE: These values can only be set and used when the instrument is set to have it's wiring configuration
        in "Independant" mode.
        NOTE: if shunt is set to internal mode, shunt resistance is ignored/ has no effect.
        """
        assert channel in [1, 2, 3]
        assert internal_or_external in ["internal", "external"]

        if internal_or_external == "internal":
            self.addr.write("CONFIG,25,1") # function 25 is range - current input; 1 specifies internal shunt

        if internal_or_external == "external":
            self.addr.write("CONFIG,25,2") # function 25 is range - current input; 2 specifies external shunt
            self.addr.write("SHUNT,CH{0},{1}".format(channel, shunt_resistance))

    def set_wiring_mode(self, wiring_mode = "INDEP"):
        """
        set the wiring mode for the instrument. Valid inputs are:
        SINGLE: only phase 1 is wired up
        2PHASE: 2 phases active + 2 wattmeters
        3PH2WA: 3 phases active + 2 wattmeters (calculate third phase)
        3PH3WA: 3 phases active + 3 wattmeters
        INDPH3: 3 phases active + 2 wattmeters + phase 3 independantly
        PHASE1: only phase 1 is active
        PHASE2: only phase 2 is active
        PHASE3: only phase 3 is active
        INDEP: independant, every phase is active but measures with disregard for others
        3PH3WA,DELTAS: For delta - star configuration
        3PH3WA,PPRMS: RMS between two phases
        3PH3WA,PPMEAN: Rectified mean
        3PH3WA,STARDE: for star - delta configuration
        """
        assert wiring_mode in ["SINGLE", "2PHASE", "3PH2WA", "3PH3WA",
                               "INDPH3", "PHASE1", "PHASE2", "PHASE3",
                               "INDEP", "3PH3WA,DELTAS", "3PH3WA,PPRMS", "3PH3WA,PPMEAN", "3PH3WA,STARDE"]

        self.addr.write("WIRING,{0}".format(wiring_mode))