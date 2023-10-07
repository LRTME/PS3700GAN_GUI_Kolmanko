import struct
import socket_creation
"""
TODO:
- set/ get trigger(single - ready) [DONE?]
- notification if signal was captured or if it's still waiting for trigger
- min/ max for each channel [DONE]
- set vertical scale and offset for each channel [DONE]
    - channel (VERTICAL) offset range
        - 1mV/div - 50mV/div = +/-1V
        - 50.5mV/div - 99.5mV/div = +/-0.5V
        - 100mV/div - 500mV/div = +/-10V
        - 505mV/div - 995mV/div = +/-5V
        - 1V/div - 5V/div = +/-100V
        - 5.05V/div - 10V/div = +/-50V
        
- set time scale [DONE]
- acquiring all values of given channel(acquired values, not shown)
- automatic setting of vertical scale and offset [DONE]
"""


class MSO7034A:

    def __init__(self, ip_or_name, socket = False, port = 0):
        self.addr = socket_creation.create_socket(ip_or_name, socket, port)

    def get_id(self):
        """
        Return the identification of set device
        TESTED: TRUE
        RESULT: WORKING
        """

        # Acquire identification
        return self.addr.query('*IDN?')

    def set_trigger_mode(self, mode = "EDGE"):
        """
        Set the trigger mode/ type. the modes can be:
        {EDGE | GLITch | PATTern | CAN | DURation | I2S |IIC
        | EBURst | LIN | M1553| SEQuence | SPI | TV | UART
        | USB | FLEXray
        For more information read pdf page 469.
        """
        assert mode in ["EDGE", "GLITCH", "PATTERN", "CAN","DURATION", "I2S",
                        "IIC", "EBURST", "LIN", "M1553", "SEQUENCE", "SPI",
                        "TV","UART", "USB", "FLEXRAY"]

        self.addr.write(":TRIGger:MODE {0}".format(mode))

    def set_trigger_sweep(self, sweep = "NORMAL"):
        """
        The :TRIGger:SWEep command selects the trigger sweep mode.
        When AUTO sweep mode is selected, a baseline is displayed in the absence
        of a signal. If a signal is present but the oscilloscope is not triggered, the
        unsynchronized signal is displayed instead of a baseline.
        When NORMal sweep mode is selected and no trigger is present, the
        instrument does not sweep, and the data acquired on the previous trigger
        remains on the screen.
        """
        assert sweep in ["AUTO", "NORMAL", "NORM"]
        self.addr.write(":TRIGger:SWEep {0}".format(sweep))

    def get_trigger_sweep(self):
        """
        The :TRIGger:SWEep? query returns the current trigger sweep mode
        """
        return self.addr.query(":TRIGger:SWEep?")

    def set_trigger_source(self, channel = 1):
        """
        sets the channel used as trigger source
        """
        assert channel in [1, 2, 3, 4, "EXTERNAL", "EXT", "LINE"]

        if channel == 1 or 2 or 3 or 4:
            self.addr.write(":TRIGger:SOURce CHAN{0}".format(channel))

        else:
            self.addr.write("TRIGger:SOURce {0}".format(channel))

    def get_trigger_source(self):
        """
        acquire currently chosen trigger source
        """
        return self.addr.query(":TRIGger:SOURce?")

    def set_trigger_coupling(self, coupling = "DC"):
        """
        Sets the trigger coupling to DC|AC|LF
        """
        assert coupling in ["AC", "DC", "LF"]
        self.addr.write(":TRIGger:COUPling {0}".format(coupling))

    def get_trigger_coupling(self):
        """
        acquire currently set trigger coupling mode
        """
        return self.addr.query(":TRIGger:COUPling?")

    def set_trigger_frequency_rejection(self, rejection = "OFF"):
        """
        set which frequency the trigger rejects. LF|HF|OFF
        HF: 50kHz low-pass filter
        LF: 50kHz high-pass filter
        """
        assert rejection in ["LF", "HF", "OFF"]
        self.addr.write(":TRIGger:REJect {0}".format(rejection))

    def get_trigger_frequency_rejection(self):
        """
        acquire currently set trigger frequency rejection
        """
        return self.addr.query("TRIGger:REJect?")

    def set_trigger_slope(self, slope = "POS"):
        """
        The :TRIGger[:EDGE]:SLOPe command specifies the slope of the edge for the trigger.
        """
        assert slope in ["NEG", "NEGATIVE", "POS", "POSITIVE", "EITH", "EITHER", "ALT", "ALTERNATIVE"]
        self.addr.write(":TRIGger:SLOPe {0}".format(slope))

    def get_trigger_slope(self):
        """
        acquire current trigger slope
        """
        self.addr.query(":TRIGger:SLOPe?")

    def trigger_single(self):
        """
        Set off a single trigger
        """
        self.addr.write(":SINGle")

    def trigger_run(self):
        """
        sets trigger to run mode
        """
        self.addr.write(":RUN")

    def trigger_stop(self):
        """
        sets trigger to stop mode
        """
        self.addr.write(":STOP")

    def set_channel_display(self, channel = 1, status = "ON"):
        """
        The :CHANnel<n>:DISPlay command turns the display of the specified channel on or off.
        """
        assert channel in [1,2,3,4]
        assert status in ["ON", 1, "OFF", 0]
        self.addr.write(":CHANnel{0}:DISPlay {1}".format(channel, status))

    def get_trigger_status(self):
        """
        returns trigger status. if ready to accept trigger, status value is set to 1. status value is cleared after
        being read.
        The AER query reads the Arm Event Register. After the Arm Event Register is read, it is cleared.
        A "1" indicates the trigger system is in the armed state, ready to accept a trigger.
        The Armed Event Register is summarized in the Wait Trig bit of the Operation Status Event Register.
        A Service Request can be generated when the Wait Trig bit transitions and the appropriate enable bits
        have been set in the Operation Status Enable Register (OPEE) and the Service Request Enable Register (SRE).
        """
        return self.addr.query(":AER?")

    def get_frequency(self, channel = 1):
        """
        get frequency for specified channel
        """
        assert channel in [1,2,3,4]
        return self.addr.query(":MEASure:FREQuency? CHANnel{0}".format(channel))

    def get_phase(self, channel = 1):
        """
        get phase for specified channel
        """
        assert channel in [1,2,3,4]
        return self.addr.query(":MEASure:PHASe? CHANnel{0}".format(channel))

    def get_voltage_max(self, channel = 1):
        """
        acquire max voltage of specified channel
        """
        assert channel in [1, 2, 3, 4]
        return self.addr.query(":MEASure:VMAX? CHAN{0}".format(channel))

    def get_voltage_min(self, channel = 1):
        """
        acquire min voltage of specified channel
        """
        assert channel in [1, 2, 3, 4]
        return self.addr.query(":MEASure:VMIN? CHAN{0}".format(channel))

    def get_voltage_amplitude(self, channel = 1):
        """
        acquire voltage amplitude of specified channel
        """
        assert channel in [1, 2, 3, 4]
        return self.addr.query(":MEASure:VAMPlitude? CHAN{0}".format(channel))

    def get_voltage_average(self, channel = 1):
        """
        acquire voltage average of specified channel
        """
        assert channel in [1, 2, 3, 4]
        return self.addr.query(":MEASure:VAVerage? CHAN{0}".format(channel))

    def get_voltage_base(self, channel = 1):
        """
        acquire base voltage of specified channel
        """
        assert channel in [1, 2, 3, 4]
        return self.addr.query(":MEASure:VBASe? CHAN{0}".format(channel))

    def get_voltage_peak_to_peak(self, channel = 1):
        """
        acquire voltage peak to peak of specified channel
        """
        assert channel in [1, 2, 3, 4]
        return self.addr.query(":MEASure:VPP? CHAN{0}".format(channel))

    def get_voltage_rms(self, channel = 1):
        """
        acquire RMS voltage of specified channel
        """
        assert channel in [1, 2, 3, 4]
        return self.addr.query(":MEASure:VRMS? CHAN{0}".format(channel))

    def set_offset_manual(self, offset = 0, channel = 1):
        """
        manually set offset for specified channel
        """
        assert channel in [1,2,3,4]
        self.addr.write(":CHANnel{0}:OFFSet {1}".format(channel, offset))

    def set_offset_automatic(self, channel = 1):
        """
        automatically set signal offset for specified channel
        """
        assert channel in [1,2,3,4]

        max_value = self.get_voltage_max(channel)
        min_value = self.get_voltage_min(channel)

        offset = (max_value - min_value)/2 + min_value

        self.set_offset_manual(offset, channel)

    def get_offset(self, channel = 1):
        """
        acquire current offset for specified channel
        """
        assert channel in [1,2,3,4]
        return self.addr.query(":CHANnel{0}:OFFSet?".format(channel))

    def set_probe_ratio(self, probe_ratio = 1, channel = 1):
        """
        set the probe ratio for specified channel. values of the probe can be from 0.1 to 1000.
        The :CHANnel<n>:PROBe command specifies the probe attenuation factor for the selected channel.
        The probe attenuation factor may be 0.1 to 1000.
        This command does not change the actual input sensitivity of the oscilloscope.
        It changes the reference constants for scaling the display factors, for making automatic measurements,
        and for setting trigger levels
        """
        assert channel in [1,2,3,4]
        if probe_ratio < 0.1:
            raise ValueError("Set probe ratio is too small. Smallest supported probe ratio is 0.1!")
        elif probe_ratio > 1000:
            raise ValueError("Set probe ratio is too big. biggest supported probe ratio is 1000!")
        else:
            self.addr.write(":CHANnel{0}:PROBe {1}".format(channel, probe_ratio))

    def get_probe_ratio(self, channel = 1):
        """
        acquire probe ratio for specified channel. values of the probe can range from 0.1 to 1000.
        """
        assert channel in [1, 2, 3, 4]
        return self.addr.query(":CHANnel{0}:PROBe?".format(channel))

    def set_vertical_scale_manual(self, vertical_scale, channel = 1, units = "V"):
        """
        sets the vertical scale of specified channel. Default units are V. can be set to mV or V.
        The :CHANnel<n>:SCALe command sets the vertical scale, or units per division, of the selected channel
        """
        assert channel in [1,2,3,4]
        assert units in ["V", "mV"]

        self.addr.write(":CHANnel{0}:SCALe {1}{2}".format(channel, vertical_scale, units))

    def set_vertical_scale_auto(self, channel = 1):
        """
        automatically set the vertical scale/ offset of specified channel. Unit is V.
        if probe is 1:1, scale can take values from 2mV to 5V.
        If the probe attenuation is changed, the scale value is multiplied by the probe's attenuation factor.
        """
        assert channel in [1, 2, 3, 4]

        # 1.) get probe ratio
        probe_ratio = self.get_probe_ratio(channel)

        # 2.) get min & max voltage values
        min_voltage = self.get_voltage_min(channel)
        max_voltage = self.get_voltage_max(channel)

        # 3.) Calculate delta
        delta = max_voltage - min_voltage

        # 4.) Divide delta with number of vertical divisions (8)
        target_gain = delta / 8

        # 5.) check if target gain is within given limits
        if target_gain < (probe_ratio * 0.002):
            target_gain = probe_ratio * 0.002
            print("WARNING: Target gain outside of minimal bounds. Set to minimal ({0}).".format(probe_ratio * 0.002))

        elif target_gain > (probe_ratio * 5):
            target_gain = probe_ratio * 5
            print("WARNING: Target gain outside of maximal bounds. Set to maximal ({0}).".format(probe_ratio * 5))

        else:
            pass
        self.addr.write(":CHANnel{0}:SCALe {1}V".format(channel, target_gain))

    def get_vertical_scale(self, channel = 1):
        """
        raturn the value of current vertical scale
        """
        assert channel in [1, 2, 3, 4]
        return self.addr.query(":CHANnel{0}:SCALe?".format(channel))

    def set_timebase_scale(self, scale = 0.02):
        """
        The :TIMebase:SCALe command sets the horizontal scale or units per division for the main window.
        Values can be from 500 ps to 50 s.
        """
        if scale < 500e-12:
            scale = 500e-12
            print("WARNING: Set time scale out of bounds. Set to minimal (500e-12s).")

        elif scale > 50:
            scale = 50
            print("WARNING: Set time scale out of bounds. Set to maximal (50s).")

        else:
            pass

        self.addr.write(":TIMebase:SCALe {0}".format(scale))

    """
    -----------------------------------------------
    ************** Waveform capture ***************
    ----------------------------------------------
    """

    def set_waveform_capture_source(self, channel):
        """
        set which channel will be source used for waveform capture
        """
        self.addr.write(":WAVEFORM:SOURCE CHAN{0}".format(channel))

    def set_waveform_capture_format(self, waveform_format):

        assert waveform_format in ["WORD", "BYTE"]

        self.addr.write(":WAVEFORM:FORMAT {0}".format(waveform_format))

    def get_waveform_capture_preamble(self):
        """
        query and return all waveform parameters
        """

        values = self.addr.query(":WAV:PRE?")
        values = values.split(",")
        assert len(values) == 10
        format, type, points, count, x_reference, y_origin, y_reference = (
            int(float(val)) for val in values[:4] + values[6:7] + values[8:10]
        )
        x_increment, x_origin, y_increment = (
            float(val) for val in values[4:6] + values[7:8]
        )
        return (
            format,
            type,
            points,
            count,
            x_increment,
            x_origin,
            x_reference,
            y_increment,
            y_origin,
            y_reference,
        )

    def get_waveform_capture_data(self):
        """
        acquire waveform data
        """
        self.addr.write(":WAVEform:DATA?")
        self.addr.Timeout = 15000
        read = self.addr.read_raw()
        return read

    def get_waveform_capture_sample_rate(self):
        """
        acquire sample rate of waveform capture
        """
        return self.addr.query(":ACQuire:SRATe?")

    def get_waveform_capture_time_scale(self):
        """
        acquire time scale
        """
        return self.addr.query(":TIMEbase:SCALe?")

    def get_waveform_capture_time_offset(self):
        """
        acquire time from the trigger event to the display reference point
        """
        return self.addr.query(":TIMEbase:POSition?")

    def set_waveform_capture_points_mode(self, mode = "NORMAL"):
        """
        <# points> ::= {100 | 250 | 500 | 1000 | <points mode>}
        if waveform points mode is NORMal
        <# points> ::= {100 | 250 | 500 | 1000 | 2000 | 5000 | 10000 | 20000
        | 50000 | 100000 | 200000 | 500000 | 1000000 | 2000000
        | 4000000 | 8000000 | <points mode>}
        if waveform points mode is MAXimum or RAW
        <points mode> ::= {NORMal | MAXimum | RAW}
        """

        assert mode in ["NORM", "NORMAL", "MAX", "MAXIMUM", "RAW"]
        self.addr.write(":WAVeform:POINts:MODE {0}".format(mode))

    def set_waveform_capture_points(self, points = 1000):
        """
        command sets the number of waveform points to be transferred with the :WAVeform:DATA? query.
        This value represents the points contained in the waveform selected with the :WAVeform:SOURce command.
        """
        points_mode = self.addr.query(":WAVEform:POINts:MODE?")
        if points_mode == "NORM":
            assert points in [100, 250, 500, 1000]

        elif points_mode == "MAX" or "RAW":
            assert points in [100, 250, 500,
                              1000, 2000, 5000,
                              10000, 20000, 50000,
                              100000, 200000, 500000,
                              1000000, 2000000, 4000000]

        else:
            raise ValueError("ERROR: Something went really wrong. This should never happen")

        self.addr.write(":WAVeform:POINts {0}".format(points))

    def get_number_of_points(self):
        return self.addr.query(":ACQuire:POINts?")

    def get_waveform(self, channel = 1, number_of_points = 1000):
        self.set_waveform_capture_source(channel)
        self.set_waveform_capture_format("BYTE")
        (
            format,
            type,
            points,
            count,
            x_increment,
            x_origin,
            x_reference,
            y_increment,
            y_origin,
            y_reference,
        ) = self.get_waveform_capture_preamble()
        self.set_waveform_capture_points_mode("RAW")
        self.set_waveform_capture_points(number_of_points)
        tmp_buff = self.get_waveform_capture_data()
        n_header_bytes = int(chr(tmp_buff[1])) + 2
        n_data_bytes = int(tmp_buff[2:n_header_bytes].decode("ascii"))
        buff = tmp_buff[n_header_bytes: n_header_bytes + n_data_bytes]
        #assert len(buff) == points
        samples = list(struct.unpack(str(len(buff)) + "B", buff))
        samples = [
            (sample - y_origin - y_reference) * y_increment for sample in samples
        ]
        timebase_scale = self.get_waveform_capture_time_scale()
        timebase_offset = self.get_waveform_capture_time_offset()
        x_axis = [
            i * float(timebase_scale) / (number_of_points/10) + float(timebase_offset)
            for i in range(len(samples))
        ]
        #x_axis = [x * (abs(x_axis[1]) + x_axis[len(x_axis) - 1]) / (100 * number_of_points) for x in range(len(x_axis))]
        return x_axis, samples  # x_axis is in seconds.

