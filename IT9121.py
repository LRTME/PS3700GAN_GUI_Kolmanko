import socket_creation

"""
TODO: 
- Change structure to class [DONE]
- make __init__ in which pyvisa socket is created using only IP [DONE]
- check if trigger refreshes voltage/current/power (set single trigger, force it and read voltage/current/power 3 times
(should all be the same), then force trigger again and read voltage/current/power again (should be different now))
"""


class IT9121:

    """
    NOTE: DEVICE CAN ONLY BE CONNECTED WITH USING IP!!! DEVICE IS NOT SHOWN IN RESOURCE LIST, THEREFORE NAME CANNOT
    BE USED!!
    DEVICE HAS TO BE USED USING SOCKET AND PORT (DEFAULT PORT = 30000) OR ELSE CONNECTION WILL NOT BE ESTABLISHED!
    """
    def __init__(self, ip_or_name, socket = True, port = 30000):
       self.addr = socket_creation.create_socket(ip_or_name, socket, port)

    def get_id(self):
        return self.addr.query("*IDN?")

    def get_base_source_voltage(self, voltage = "DC"):

        assert voltage in ["DC", "AC"]
        if voltage == "DC":

            return self.addr.query("MEAS:VOLT:DC?")

        else:
            return self.addr.query("MEAS:VOLT:AC?")

    def get_RMS_source_voltage(self):

        return self.addr.query("MEAS:VOLT:RMS?")

    def get_THD_source_voltage(self):

        return self.addr.query("MEAS:HARM:VOLT:THD?")

    def get_base_source_current(self, voltage = "DC"):

        assert voltage in ["AC", "DC"]
        if voltage == "DC":
            return self.addr.query("MEAS:CURR:DC?")
        else:
            return self.addr.query("MEAS:CURR:AC?")


    def get_RMS_source_current(self):

        return self.addr.query("MEAS:CURR:RMS?")

    def get_THD_source_current(self):

        return self.addr.query("MEAS:HARM:CURR:THD?")

    def get_active_power(self):

        return self.addr.query("MEAS:POW:ACT?")

    def get_apparent_power(self):

        return self.addr.query("MEAS:POW:APP?")

    def get_power_THD(self):

        return self.addr.query("MEAS:HARM:POW:THD?")

    def get_reactive_power(self):

        return self.addr.query("MEAS:POW:REAC?")

    def get_power_factor(self):

        return self.addr.query("MEAS:POW:PFAC?")

    def get_phase(self):

        return self.addr.query("MEAS:POW:PHAS?")

    def start_waveform_capture(self):
        """
        sets waveform capture to "RUN"
        instrument is set to remote, enabling the write command to take effect
        instrument is then set back to local, enabling the function of physical buttons
        """

        self.set_system_remote()
        self.addr.write("WAVE:RUN")
        self.set_system_local()

    def stop_waveform_capture(self):
        """
        sets the waveform capture to "STOP"
        instrument is set to remote, enabling the write command to take effect
        instrument is then set back to local, enabling the function of physical buttons
        """

        self.set_system_remote()
        self.addr.write("WAVE:STOP")
        self.set_system_local()

    def single_waveform_capture(self): # $$ DOESN'T WORK? $$
        """
        used to trigger a single waveform capture
        instrument is set to remote, enabling the write command to take effect
        instrument is then set back to local, enabling the function of physical buttons
        """

        self.set_system_remote()
        self.addr.write("WAVE:SINGLE")
        self.set_system_local()

    def get_trigger_state(self):
        """
        get trigger status. possible returns:
        Auto|Auto?|Trig|Trig?|Stop
        """

        return self.addr.query("WAVE:TRIG:STAT?")

    def set_trigger_source(self, source = "VOLT"):
        """
        set which kind of waveform as trigger source. Possible inputs:
        VOLT|CURR|EXT|BUS|IMM
        instrument is set to remote, enabling the write command to take effect
        instrument is then set back to local, enabling the function of physical buttons
        """

        assert source in ["VOLT", "CURR", "EXT", "BUS", "IMM"]
        self.set_system_remote()
        self.addr.write("WAVE:TRIG:SOUR {0}".format(source))
        self.set_system_local()

    def get_trigger_source(self):
        """
        read trigger source. Possible returns:
        VOLT|CURR|EXT
        """

        return self.addr.query("WAVE:TRIG:SOUR?")

    def set_trigger_slope(self, slope = "ANY"):
        """
        set what type of slope will set off the trigger. Possible inputs: POS|NEG|ANY
        instrument is set to remote, enabling the write command to take effect
        instrument is then set back to local, enabling the function of physical buttons
        """

        assert slope in ["POS", "NEG", "ANY"]
        self.set_system_remote()
        self.addr.write("WAVE:TRIG:SLOP {0}".format(slope))
        self.set_system_local()

    def get_trigger_slope(self):
        """
        read trigger source. Possible returns:
        POS|NEG|ANY
        """

        return self.addr.query("WAVE:TRIG:SLOP?")

    def set_trigger_mode(self, mode = "AUTO"):
        """
        set what type of trigger mode the instrument will work in. Possible inputs:
        AUTO: Trigger will be forced regardless if trigger conditions are met
        NORM: Trigger will occur only if conditions are met
        """

        assert mode in ["AUTO", "NORM"]
        self.set_system_remote()
        self.addr.write("WAVE:TRIG:MODE {0}".format(mode))
        self.set_system_local()

    def get_trigger_mode(self):

        return self.addr.query("WAVE:TRIG:MODE?")

    def get_waveform_voltage(self):

        return self.addr.query("WAVE:VOLT:DATA?")

    def get_waveform_current(self):

        return self.addr.query("WAVE:CURR:DATA?")

    def get_waveform_current_and_voltage(self):
        """
        in a single waveform capture get voltage and current. Returns array of normalized values.
        """

        self.single_waveform_capture()
        voltage = self.get_waveform_voltage()
        current = self.get_waveform_current()
        return voltage, current

    def set_system_remote(self):
        """
        puts instrument into remote mode, enabling parameter changing functions to occur. This function in turn disables
        the physical buttons (except Esc; holding down Esc for 5s will enable local mode) and allows only remote control
        """

        self.addr.write("SYST:REM")

    def set_system_local(self):
        """
        puts instrument into local mode, enabling physical buttons and disabling possibility of remote operations.
        """

        self.addr.write("SYST:LOC")
