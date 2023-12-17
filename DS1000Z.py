import struct
import time
import socket_creation


class DS1000Z:

    """
    offset ranges acquired via pdf pg. 27, depending on probe ratio and current vertical scale/ gain.
    offset ranges span from - to + value.
    TODO: WIP
    Nemec instructions/ conversation file 2023-06-28_dopolnitve_k_kodi.ogg @ 19:00
    """
    def __init__(self, ip_or_name, socket = False, port = 0):
        self.addr = socket_creation.create_socket(ip_or_name, socket, port)

    def _interpret_channel(self, channel):
        """
        allows specifying channel in str or int
        """
        if type(channel) == int:
            assert channel <= 4 and channel >= 1
            channel = "CHAN" + str(channel)
        return channel

    def _masked_float(self, number):
        """
        Transforms number into float
        """
        number = float(number)
        if number == 9.9e37:
            return None
        else:
            return number

    def get_id(self):
        """
        Return the identification of set device
        TESTED: TRUE
        RESULT: WORKING
        """

        # Acquire identification
        return self.addr.query('*IDN?')

    def run(self):
        """
        sets the oscilloscope to 'RUN' mode
        """
        self.addr.write(':RUN')

    def stop(self):
        """
        sets oscilloscope to 'STOP' mode
        """
        self.addr.write(":STOP")

    def get_vertical_scale(self, channel = 1):
        """
        acquire vertical scale for specified channel
        TODO: TEST FUNCTION
        TESTED: TRUE
        RESULT: WORKING
        """
        channel = self._interpret_channel(channel)
        return self.addr.query("{0}:SCAL?".format(channel))

    def get_enabled_analog_channels(self):
        """
        check which analog channels are enabled
        TODO: TEST FUNCTION
        TESTED: TRUE
        RESULT: WORKING
        """

        enabled_channels = []
        for channel_number in range(1,5): # go through all channels (DS1000Z has 4 analog channels)
            response = self.get_max_voltage(channel_number) # Send to oscilloscope if channel enabled
            if response is not None: # if oscilloscope response contains "on", add channel to array
                enabled_channels.append(channel_number)
        return enabled_channels

    def set_memory_depth(self):
        """
        sets the maximum memory depth based on enabled analog channels for maximum resolution
        TODO: TEST FUNCTION
        TESTED: TRUE
        RESULT: WORKING
        """
        memory_depth_options = [24000000, 12000000, 6000000, 6000000] # max memory depth based on enabled channels
        enabled_analog_channels = self.get_enabled_analog_channels() # check which analog channels are enabled
        memory_depth = memory_depth_options[len(enabled_analog_channels)] #choose memory depth based on enabled channels
        self.addr.write(":ACQ:MDEP {0}".format(memory_depth))

    def set_trigger_mode(self, mode="AUTO"):
        """
        Set trigger mode. Possible inputs:
        SING: Oscilloscope waits for a trigger and displays the waveform when the trigger condition is met and then stops
        NORM: Display waveform when trigger condition is met; otherwise oscilloscope holds original waveform and waits for next trigger
        AUTO: no matter the trigger condition, waveform will always be shown
        Rigol-DS1000Z-ProgrammingGuide.pdf 2-164 \
        function calls instruction class that runs the predefined instruction based on input of mode
        TESTED: TRUE
        RESULT: WORKING
        """

        assert mode in ["AUTO", "NORM", "SING"]
        self.addr.write(":TRIG:SWE {0}".format(mode))

    def get_trigger_mode(self):
        """
        check the current trigger sweep mode
        TESTED: TRUE
        RESULT: WORKING
        """

        return self.addr.query(":TRIG:SWE?")

    def get_trigger_status(self):
        """
         Check the status of trigger if waveform was captured of if oscilloscope is still waiting for trigger
         possible returns are:
         TD: Trigger delay has expired after a trigger was recognized
         WAIT: Waiting for trigger
         RUN: Waveform has been captured/ is being captured
         AUTO: The trigger mode is set to AUTO - see set_trigger_sweep for more info
         STOP: Waveform is no longer being captured/ trigger condition no longer met
        TESTED: TRUE
        RESULT: WORKING
         """

        return self.addr.query("TRIGger:STATus?")

    def trigger(self):
        self.addr.write(":TRIGger:IMM")

    def get_measurement(self, item = "VMAX", type="CURR", channel=1):
        """
        get desired measurement.
        TESTED: TRUE
        RESULT: WORKING
        """

        channel = self._interpret_channel(channel)
        assert type in ["MAX", "MIN", "CURR", "AVER", "DEV"]
        assert item in [
            "VMAX",
            "VMIN",
            "VTOP",
            "VBAS",
            "VAMP",
            "VAVG",
            "VRMS",
            "OVER",
            "PRES",
            "MAR",
            "MPAR",
            "PER",
            "FREQ",
            "RTIM",
            "FTIM",
            "PWID",
            "NWID",
            "PDUT",
            "NDUT",
            "RDEL",
            "FDEL",
            "RPH",
            "FPH",
        ]
        return self._masked_float(
            self.addr.query(":MEAS:STAT:ITEM? {0},{1},{2}".format(type, item, channel), 0.02)
        )

    def get_max_voltage(self, channel=1):
        """
        returns the max voltage value for specified channel
        TESTED: TRUE
        RESULT: WORKING
        """

        max_value = self.get_measurement("VMAX", "MAX", channel)
        time_start = time.perf_counter()

        while max_value is None:
            max_value = self.get_measurement("VMAX", "MAX", channel)

            if ((1 + time_start) - time.perf_counter()) <= 0:
                return max_value

        return max_value

    def get_min_voltage(self, channel=1):
        """
        returns the min voltage value for specified channel
        TESTED: TRUE
        RESULT: WORKING
        """

        min_value = self.get_measurement("VMIN", "MIN", channel)
        time_start = time.perf_counter()

        while min_value is None:
            min_value = self.get_measurement("VMIN", "MIN", channel)

            if ((1 + time_start) - time.perf_counter()) <= 0:
                return min_value

        return min_value

    def get_probe_ratio(self, channel=1):
        """
        acquire probe ratio for specified channel
        TESTED: TRUE
        RESULT: WORKING
        """

        channel = self._interpret_channel(channel)
        return self._masked_float(self.addr.query(":{0}:PROBe?".format(channel)))

    def set_auto_vertical_scale(self, min_value, max_value, channel=1):
        """
        automatically set vertical scale for set channel
        TODO: [DONE] Test how it works if signal is way too big (out of bounds - nasičen) NOTE: Nothing happens
        TODO: [?] Make sure that new capture happens with each iteration -> force trigger -> run mode -> single, so new
        capture can be seen via TRIG:STATus
        TESTED: TRUE
        RESULT: WORKING
        """

        true_gain = 0

        # if either min_value or max_value are out of bounds (are None), return error (for now; change in future?)
        if min_value is None or max_value is None:
            raise ValueError("Signal out of bounds. Please run the auto_scale_and_auto_offset function or manually "
                             "adjust signal.")

        delta = max_value - min_value  #
        target_gain = delta / 8  # oscilloscope has 8 vertical divisions

        scale_array = [1e-2, 2e-2, 5e-2, 1e-1, 2e-1, 5e-1, 1, 2, 5, 1e1, 2e1, 5e1, 1e2, 2e2, 5e2, 1e4]

        for array_range in range(len(scale_array)):
            if target_gain > scale_array[array_range]:
                array_range += 1
            else:
                true_gain = scale_array[array_range]
                break

        self.manual_vertical_scale(true_gain, channel)

    def set_auto_offset(self, min_value, max_value, channel=1):
        """
        automatically set offset for set channel
        TODO: [DONE] check if you're within limits(?). if not at least return an error
        TODO: TEST FUNCTION
        TESTED: TRUE
        RESULT: WORKING
        """
        if min_value is None or max_value is None:
            raise ValueError("Signal out of bounds. Please run auto_scale_and_auto_offset function or manually adjust"
                             " signal size.")

        probe_ratio = float(self.get_probe_ratio(channel))
        vertical_scale = float(self.get_vertical_scale(channel))

        offset = (max_value - min_value) / 2 + min_value

        if probe_ratio == 1:
            if vertical_scale >= 500e-3:

                if offset < -100:
                    offset = -100

                elif offset > 100:
                    offset = 100
                else:
                    pass

            if vertical_scale < 500e-3:
                if offset < -2:
                    offset = -2

                elif offset > 2:
                    offset = 2
                else:
                    pass

        if probe_ratio == 10:
            if vertical_scale >= 5:

                if offset < -1000:
                    offset = -1000

                elif offset > 1000:
                    offset = 1000
                else:
                    pass

            if vertical_scale < 5:
                if offset < -20:
                    offset = -20

                elif offset > 20:
                    offset = 20
                else:
                    pass

        self.manual_offset(-1 * offset, channel)

    def autoscale_and_auto_offset(self, channel=1):
        """
        autoscales vertical scale and offset for spceified channel based on min and max values
        TODO: Change offset step to be based on min/max value (example: max value is 300mV -> step is 1mV)
        TESTED: TRUE
        RESULT: WORKING
        """

        min_value = self.get_min_voltage(channel)
        max_value = self.get_max_voltage(channel)

        if min_value is None or max_value is None:

            self.manual_offset(0, channel)  # Offset set to 0
            self.manual_vertical_scale(1e4, channel)  # Scale set to max

            min_value = self.get_min_voltage(channel)

            max_value = self.get_max_voltage(channel)

            # if max value cannot be acquired, move the entire signal downwards until the limit
            if max_value is None:

                offset = 0
                while offset <= 8 * 1e4:  # 8*1e4 chosen because signal cannot be bigger than 1e4 per vertical division

                    self.manual_offset(-1 * offset, channel)
                    offset += 0.2
                    max_value = self.get_max_voltage(channel)
                    if max_value is not None:
                        return max_value

            # if min value cannot be acquired, move the entire signal upwards until the limit
            if min_value is None:

                offset = 0
                while offset <= 8 * 1e4:  # 8*1e4 chosen because signal cannot be bigger than 1e4 per vertical division

                    self.manual_offset(offset, channel)
                    offset += 0.2
                    max_value = self.get_min_voltage(channel)
                    if min_value is not None:
                        return min_value

            if min_value is None and max_value is None:
                return "Error: Could not get minimal or maximal value. The measured signal may be too big."

            else:
                pass

        if min_value is not None and max_value is not None:

            # set scale and offset off of gotten measurements
            self.set_auto_vertical_scale(min_value, max_value, channel)
            self.set_auto_offset(min_value, max_value, channel)

            # Recapture min/max for better resolution
            min_value = self.get_min_voltage(channel)

            max_value = self.get_max_voltage(channel)

            # Re-set scale and offset off of better resolution measurements
            self.set_auto_vertical_scale(min_value, max_value, channel)
            self.set_auto_offset(min_value, max_value, channel)

        else:
            print("Error: This should never happen.")

    def manual_vertical_scale(self, scale=1, channel=1):
        """
        Manual vertical scale setting. It can accept the following values:
        [1e-2, 2e-2, 5e-2, 1e-1, 2e-1, 5e-1, 1, 2, 5, 1e1, 2e1, 5e1, 1e2, 2e2, 5e2, 1e4]
        TESTED: TRUE
        RESULT: WORKING
        """

        channel = self._interpret_channel(channel)
        possible_scales = [
            val * self.get_probe_ratio(channel)
            for val in [1e-2, 2e-2, 5e-2, 1e-1, 2e-1, 5e-1, 1, 2, 5, 1e1, 2e1, 5e1, 1e2, 2e2, 5e2, 1e4]
        ]
        scale = min(possible_scales, key=lambda x: abs(x - scale))
        self.addr.write(":{0}:SCALe {1}".format(channel, scale))

    def manual_offset(self, offset=0, channel=1):
        """
        Manual offset setting
        TESTED: TRUE
        RESULT: WORKING
        """

        channel = self._interpret_channel(channel)
        self.addr.write(":{0}:OFFSet {1}".format(channel, offset))

    def set_waveform_source(self, channel=1):
        """
        set the channel from which the waveform will be read
        """

        channel = self._interpret_channel(channel)
        self.addr.write(":WAV:SOUR {0}".format(channel))

    def set_waveform_format(self, format="BYTE"):

        assert format in ["WORD", "BYTE", "ASC"]
        self.addr.write(":WAV:FORM {0}".format(format))

    def get_waveform_preamble(self):
        """
        query and return all waveform parameters
        """

        values = self.addr.query(":WAV:PRE?")
        values = values.split(",")
        assert len(values) == 10
        format, type, points, count, x_reference, y_origin, y_reference = (
            int(val) for val in values[:4] + values[6:7] + values[8:10]
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

    def set_waveform_start(self, start=1):
        """
        Set the start position of internal memory waveform reading.
        """

        self.addr.write(":WAV:STAR {0}".format(start))

    def set_waveform_stop(self, stop=1200):
        """
        Set the stop position of internal memory waveform reading.
        Max value is 250 000 (in data type BYTE).
        Total points depends on memory depth, which can be up to 24 000 000 points (pdf 21).
        See example 2 in pdf page 241.
        If the memory depth exceeds the set max value, the signal needs to be captured in multiple batches
        """

        self.addr.write(":WAV:STOP {0}".format(stop))

    def get_waveform_data(self):
        """
        read waveform data
        """

        self.addr.write(":WAV:DATA?")
        output = self.addr.read_raw()
        return output

    def get_timebase_scale(self):
        """
        Query the delayed timebase scale. The default unit is s/div.
        """

        return self._masked_float(self.addr.query(":TIMebase:MAIN:SCALe?"))

    def get_timebase_offset(self):
        """
        Query the delayed timebase offset. The default unit is s.
        """

        return self._masked_float(self.addr.query(":TIMebase:MAIN:OFFSet?"))

    def capture_waveform(self, channel=1, number_of_points = 1200):
        """
        Returns waveform in text form stored as a 2D array
        TODO: [DONE] check if acquired waveform matches that on screen in scale. set time scale to smallest and to biggest and
        try capturing signal both times.
        TODO (MAYBE): Automatically set number_of_points based on memory_depth
        NOTES: Time scale is 10x too large. [FIXED]
        TESTED: TRUE
        RESULT: WORKING
        """

        # Interpret the channel number
        channel = self._interpret_channel(channel)
        # Set the waveform source based on the interpreted channel
        self.set_waveform_source(channel)
        # Set the waveform format to BYTE
        self.set_waveform_format("BYTE")
        # Retrieve waveform details like format, type, etc.
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
        ) = self.get_waveform_preamble()
        # Set the start and stop points for data capture
        self.set_waveform_start(1)
        self.set_waveform_stop(number_of_points)
        # Retrieve the waveform data
        tmp_buff = self.get_waveform_data()
        # Determine the number of header bytes and data bytes
        """
        "tmp_buff" contains the raw data retrieved from the instrument or source.
        "tmp_buff[1]" accesses a specific byte in the data.
        This integer represents the number of header bytes
        + 2 is the protocol or data format standard that adds additional number of bytes reserved for headers beyond
        what's explicitly indicated by the converted integer byte.
        """
        n_header_bytes = int(chr(tmp_buff[1])) + 2
        n_data_bytes = int(tmp_buff[2:n_header_bytes].decode("ascii"))
        # Extract the data from the buffer
        buff = tmp_buff[n_header_bytes: n_header_bytes + n_data_bytes]
        # Ensure the extracted data length matches the expected number of points
        assert len(buff) == points
        # Unpack the data into samples
        samples = list(struct.unpack(str(len(buff)) + "B", buff))
        # Adjust the samples based on y-axis properties
        samples = [
            (sample - y_origin - y_reference) * y_increment for sample in samples
        ]
        # Retrieve timebase scale and offset
        timebase_scale = self.get_timebase_scale()
        timebase_offset = self.get_timebase_offset()
        # Generate the x-axis values (time in seconds)
        x_axis = [
            i * timebase_scale / 100.0 + timebase_offset
            for i in range(-len(samples) // 2, len(samples) // 2)
        ]
        # Adjust x-axis values based on the number of points
        x_axis = [x * (abs(x_axis[1]) + x_axis[len(x_axis) - 1]) / number_of_points for x in range(len(x_axis))]
        # Return the x-axis (time in seconds) and samples (amplitude values)
        return x_axis, samples  # x_axis is in seconds.
