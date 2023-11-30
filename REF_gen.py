# -*- coding: utf-8 -*-
import struct


class REF_generator():
    def __init__(self, parent):
        self.app = parent

        self.app.commonitor.connect_rx_handler(0x0B0A, self.on_ref_params_received)

        # connect and configure reference generator items
        self.app.naklon_spin.setOpts(value=100, dec=True, step=1, minStep=1, int=True, decimals=4)
        self.app.naklon_spin.setMinimum(1)
        self.app.naklon_spin.setMaximum(10000)
        self.app.naklon_spin.valueChanged.connect(self.naklon_changed)
        self.app.frekvenca_spin.valueChanged.connect(self.ref_freq_changed)

        self.ref_range = 1
        self.app.amp_spin.valueChanged.connect(self.ref_amp_spin_changed)
        self.app.amp_spin.setSingleStep(0.01)
        self.app.sld_amp.valueChanged[int].connect(self.ref_amp_slider_changed)
        self.app.sld_amp.sliderReleased.connect(self.request_ref_params)
        self.app.sld_amp.setMaximum(self.ref_range * 100)

        self.app.sld_offset.valueChanged[int].connect(self.ref_offset_changed)
        self.app.sld_offset.sliderReleased.connect(self.request_ref_params)
        self.app.sld_duty.valueChanged[int].connect(self.ref_duty_changed)
        self.app.sld_duty.sliderReleased.connect(self.request_ref_params)
        self.app.oblika_sel.currentIndexChanged.connect(self.type_changed)
        self.app.clock_sel.currentIndexChanged.connect(self.clock_shanged)
        self.app.harmonik_spin.setOpts(value=1, dec=True, step=1, minStep=1, int=False)
        self.app.harmonik_spin.setMinimum(1)
        self.app.harmonik_spin.setMaximum(100)
        self.app.harmonik_spin.valueChanged.connect(self.ref_harm_changed)
        self.app.mode_sel.currentIndexChanged.connect(self.mode_changed)
        self.app.cycle_number_spin.setOpts(value=1, dec=True, step=1, minStep=1, int=False)
        self.app.cycle_number_spin.setMinimum(1)
        self.app.cycle_number_spin.setMaximum(100)
        self.app.cycle_number_spin.valueChanged.connect(self.ref_cycle_changed)
        self.app.btn_ref_single_shot.clicked.connect(self.btn_single_shot_clicked)

        # if com port is open, request parameters for initial update of GUI
        if self.app.commonitor.is_port_open():
            self.request_ref_params()
        else:
            self.app.commonitor.register_on_open_callback(self.request_ref_params)

    def mode_changed(self):
        if self.app.mode_sel.currentIndex() == 0:
            self.app.cycle_number_spin.setEnabled(False)
            self.app.btn_ref_single_shot.setEnabled(False)
            self.app.lbl_cycle_number.setEnabled(False)
            self.app.lbl_reg_gen_mode.setEnabled(False)
        else:
            self.app.cycle_number_spin.setEnabled(True)
            self.app.btn_ref_single_shot.setEnabled(True)
            self.app.lbl_cycle_number.setEnabled(True)
            self.app.lbl_reg_gen_mode.setEnabled(True)

        mode = struct.pack('<h', int(self.app.mode_sel.currentIndex()))
        self.app.commonitor.send_packet(0x0B1C, mode)

    def ref_cycle_changed(self):
        # send packet
        cycles = int(self.app.cycle_number_spin.value())
        data = struct.pack('<h', cycles)
        self.app.commonitor.send_packet(0x0B1B, data)

    def btn_single_shot_clicked(self):
        # if in freeruning mode, button click does not make sense
        if self.app.mode_sel.currentIndex() == 0:
            pass
        else:
            if self.app.lbl_reg_gen_mode.text() == "Stopped":
                self.app.commonitor.send_packet(0x0B1D, struct.pack('<h', 0x0001))
            if self.app.lbl_reg_gen_mode.text() == "Running":
                self.app.commonitor.send_packet(0x0B1D, struct.pack('<h', 0x0000))

    def on_ref_params_received(self):
        # grab packet date
        data = self.app.commonitor.get_data()

        # parse packet data
        amp = struct.unpack('<f', data[0:4])[0]
        offset = round(struct.unpack('<f', data[4:8])[0], 2)
        freq = round(struct.unpack('<f', data[8:12])[0], 1)
        duty = round(struct.unpack('<f', data[12:16])[0], 2)
        slew = round(struct.unpack('<f', data[16:20])[0], 0)

        type = struct.unpack('<h', data[20:22])[0]
        clock = struct.unpack('<h', data[22:24])[0]
        harmonic = struct.unpack('<h', data[24:26])[0]

        mode = struct.unpack('<h', data[26:28])[0]
        state = struct.unpack('<h', data[28:30])[0]
        periods = struct.unpack('<h', data[30:32])[0]

        # update GUI widgets
        self.app.frekvenca_spin.blockSignals(True)
        self.app.frekvenca_spin.setValue(freq)
        self.app.frekvenca_spin.blockSignals(False)

        self.app.sld_amp.blockSignals(True)
        self.app.sld_amp.setValue(int(round(amp * self.ref_range * 100, 0)))
        self.app.sld_amp.blockSignals(False)
        self.app.amp_spin.blockSignals(False)
        self.app.amp_spin.setValue(round(40 * self.app.sld_amp.value() / (self.ref_range * 100), 2))
        self.app.amp_spin.blockSignals(False)

        self.app.sld_offset.blockSignals(True)
        self.app.sld_offset.setValue(int(round(offset*100, 0)))
        self.app.sld_offset.blockSignals(False)
        self.app.lbl_offset.setText(str(self.app.sld_offset.value() / 100))

        self.app.sld_duty.blockSignals(True)
        self.app.sld_duty.setValue(int(round(duty*100, 0)))
        self.app.sld_duty.blockSignals(False)
        self.app.lbl_duty.setText(str(self.app.sld_duty.value() / 100))

        self.app.naklon_spin.blockSignals(True)
        self.app.naklon_spin.setValue(slew)
        self.app.naklon_spin.blockSignals(False)

        self.app.oblika_sel.blockSignals(True)
        self.app.oblika_sel.setCurrentIndex(type)
        self.app.oblika_sel.blockSignals(False)

        self.app.clock_sel.blockSignals(True)
        self.app.clock_sel.setCurrentIndex(clock)
        self.app.clock_sel.blockSignals(False)

        self.app.harmonik_spin.blockSignals(True)
        self.app.harmonik_spin.setValue(harmonic)
        self.app.harmonik_spin.blockSignals(False)

        # enable disable frequency/harmonic widgets
        if clock == 0:
            self.app.harmonik_spin.setEnabled(False)
            self.app.frekvenca_spin.setEnabled(True)
        else:
            self.app.harmonik_spin.setEnabled(True)
            self.app.frekvenca_spin.setEnabled(False)

        self.app.mode_sel.blockSignals(True)
        self.app.mode_sel.setCurrentIndex(mode)
        self.app.mode_sel.blockSignals(False)

        if self.app.mode_sel.currentIndex() == 0:
            self.app.cycle_number_spin.setEnabled(False)
            self.app.btn_ref_single_shot.setEnabled(False)

        else:
            self.app.cycle_number_spin.setEnabled(True)
            self.app.btn_ref_single_shot.setEnabled(True)

        if state == 0:
            self.app.lbl_reg_gen_mode.setText("Stopped")
        else:
            self.app.lbl_reg_gen_mode.setText("Running")

        self.app.cycle_number_spin.blockSignals(True)
        self.app.cycle_number_spin.setValue(periods)
        self.app.cycle_number_spin.blockSignals(False)

    def ref_amp_range(self, amp_range):
        self.ref_range = amp_range
        self.app.sld_amp.setMaximum(self.ref_range * 100)

    def ref_amp_spin_changed(self):
        # refresh the slider
        value = self.app.amp_spin.value()
        self.app.sld_amp.setValue(int(round(value * self.ref_range * 100 / self.ref_range, 0)))

    def ref_amp_slider_changed(self):
        # refresh the spinbox
        self.app.amp_spin.blockSignals(False)
        self.app.amp_spin.setValue(round(self.ref_range * self.app.sld_amp.value() / (self.ref_range * 100), 2))
        self.app.amp_spin.blockSignals(False)
        # send packet
        data = pack_Float_As_U_Long(self.app.sld_amp.value() / (self.ref_range * 100))
        self.app.commonitor.send_packet(0x0B10, data)

    def ref_offset_changed(self):
        # refresh the label
        self.app.lbl_offset.setText(str(self.app.sld_offset.value() / 100))
        # send packet
        data = pack_Float_As_U_Long(self.app.sld_offset.value() / 100)
        self.app.commonitor.send_packet(0x0B11, data)

    def ref_freq_changed(self):
        # send packet
        data = struct.pack('<f', self.app.frekvenca_spin.value())
        self.app.commonitor.send_packet(0x0B12, data)

    def ref_harm_changed(self):
        # send packet
        harm = int(self.app.harmonik_spin.value())
        data = struct.pack('<h', harm)
        self.app.commonitor.send_packet(0x0B17, data)

    def ref_duty_changed(self):
        # refresh the label
        self.app.lbl_duty.setText(str(self.app.sld_duty.value() / 100))
        # send packet
        data = pack_Float_As_U_Long(self.app.sld_duty.value() / 100)
        self.app.commonitor.send_packet(0x0B13, data)

    def naklon_changed(self):
        # send packet
        data = struct.pack('<f', int(self.app.naklon_spin.value()))
        self.app.commonitor.send_packet(0x0B14, data)

    def type_changed(self):
        data = struct.pack('<h', int(self.app.oblika_sel.currentIndex()))
        self.app.commonitor.send_packet(0x0B15, data)

    def clock_shanged(self):
        data = struct.pack('<h', int(self.app.clock_sel.currentIndex()))
        self.app.commonitor.send_packet(0x0B16, data)

    def request_ref_params(self):
        self.app.commonitor.send_packet(0x0B1A, None)

# support function
def pack_Float_As_U_Long(value):
    """ Pack a float as little endian packed data"""
    return struct.pack('<f', value)
