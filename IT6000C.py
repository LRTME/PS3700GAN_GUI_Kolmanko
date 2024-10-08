import socket_creation



class IT6000C():

    """
    def monkey_write(self, str):
        # logiraš v datoteko
        print(time.clock() + str)
        # potem pa writaš na socket
        self.addr._write(str)

    def __init__(self, ip_or_name, socket = False, port = 0):
        self.instance = socket_creation.create_socket(ip_or_name, socket, port)
        self.addr = self.instance
        self.addr._write = self.addr.write
        self.addr.write = self.monkey_write

    """
    def __init__(self, ip_or_name, socket = False, port = 0):
        self.addr = socket_creation.create_socket(ip_or_name, socket, port)


    def get_id(self):
        return self.addr.query("*IDN?")

    def set_system_remote(self):

        self.addr.write("SYST:REM")

    def set_system_local(self):

        self.addr.write("SYST:LOC")

    def set_overcurrent_protection_on_off(self, status = "OFF"):
        assert status in [1, 0, "ON", "OFF"]
        self.addr.write("SOURce:CURRent:OVER:PROTection:STATe {0}".format(status))

    def get_overcurrent_protection(self):
        return self.addr.query("SOURce:CURRent:OVER:PROTection:STATe?")

    def set_current_limit_positive(self, positive):

        if positive > 300 or positive < 0:
            raise ValueError("ERROR: Set current limit outside of bounds! Current can be between 0A and 300A!")

        self.addr.write("CURR:LIM {0}".format(positive))

    def get_current_limit_positive(self):
        return self.addr.query("CURR:LIM?")

    def get_current_limit_negative(self):
        return self.addr.query("CURR:LIM:NEG?")

    def set_current_limit_negative(self, negative):

        if negative < -300 or negative > 0:
            raise ValueError("ERROR: Set current limit outside of bounds! Current can be between 0A and -300A!")

        self.addr.write("CURR:LIM:NEG {0}".format(negative))

    def set_current_limits(self, positive, negative):
        """
        set the positive and negative current limit. Possible inputs:
        MINimum: 0A/ -300A
        MAXimum: 300A
        DEFault: 1% of instruments rated current (3A)
        <desired value between MIN and MAX>: Between -300A and 300A
        """
        self.set_current_limit_positive(positive)
        self.set_current_limit_negative(negative)

    def set_overcurrent_limit(self, limit = "MIN"):
        """
        set the current limit for over-current protection. Overcurrent protection needs to be set to ON for this
        to have effect. Possible inputs:
        MINimum: 0A
        MAXimum: 300A
        DEFault: Rated current of the instrument
        <desired value between MIN and MAX>: Between 0A and 300A
        """
        if limit > 300:
            raise ValueError("ERROR: Set current too high! Instrument supports currents of up to 300A!")

        self.addr.write("SOURce:CURRent:OVER:PROTection:LEVel {0}".format(limit))


    def get_current_limit(self):
        return self.addr.query("SOURce:CURRent:OVER:PROTection:LEVel?")

    def set_output(self, state = "OFF"):
        assert state in ["ON", "OFF", 0, 1]

        self.addr.write("OUTPut {0}".format(state))

    def set_output_voltage(self, voltage = 0.1):
        """
        Set the output voltage of instrument. Possible inputs:
        MINimum: 0V
        MAXimum: 80V
        DEFault: 1 % of rated voltage of instrument (8V)
        <desired value between MIN and MAX>: between 0V and 80V
        """
        self.addr.write("VOLT {0}".format(voltage))

    def get_output_voltage(self):
        return self.addr.query("FETCh:VOLTage?")

    def set_positive_voltage_slew(self, slew_in_seconds):
        """
        sets the rise time of output voltage (positive). The setting is in seconds.Also accepts MIN, MAX and DEFault
        Default slew rate: 0.1s
        On this instrument, slew rate means time the instrument takes to reach set/ desired voltage. For example,
        having slew rate set to 1 second means the instrument will reach set voltage of example 24V in 1 second
        """
        self.addr.write("VOLTage:SLEW:POSitive {0}".format(slew_in_seconds))

    def set_negative_voltage_slew(self, slew_in_seconds):
        """
        sets the fall time of output voltage (negative). The setting is in seconds.Also accepts MIN, MAX and DEFault
        Default slew rate: 0.1s
                On this instrument, slew rate means time the instrument takes to reach set/ desired voltage. For example,
        having slew rate set to 1 second means the instrument will reach set voltage of example 24V in 1 second
        """
        self.addr.write("VOLTage:SLEW:NEGative {0}".format(slew_in_seconds))

    def set_output_state(self, state = "ON"):
        assert state in ["ON", "OFF", 1, 0]
        self.addr.write("OUTP {0}".format(state))

    def get_output_state(self):
        return self.addr.query("OUTP?")

    def set_output_current(self, current = "MIN"):
        """
        Set output current of device. Possible inputs:
        MINimum: 0A
        MAXimum: 300A
        DEFault: Rated current of the instrument
        <desired value between MIN and MAX>: Between 0A and 300A
        """
        if current > 300:
            raise ValueError("ERROR: Set current too high! Instrument supports currents of up to 300A!")

        self.addr.write("CURRent {0}".format(current))

    def get_output_current(self):
        return self.addr.query("CURRent?")

    def get_output_power(self):
        return self.addr.query("FETCh:POWer?")

    def read_error(self):
        return self.addr.query("SYSTem:ERRor?")

