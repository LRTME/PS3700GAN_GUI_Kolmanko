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