# -*- coding: utf-8 -*-
# Import the PyQt4 module we'll need
from PyQt5 import QtWidgets, QtGui, QtCore

import math
# for ploting
import pyqtgraph as pg
# for data packing and unpacking
import struct
import numpy as np

# for timescale of the plot
SAMP_FREQ = 20000


class DLOG_viewer():

    # list for storing plot data
    ch1_latest = np.array([0.0, 0.0001])
    ch2_latest = np.array([0.0, 0.0001])
    ch3_latest = np.array([0.0, 0.0001])
    ch4_latest = np.array([0.0, 0.0001])
    ch5_latest = np.array([0.0, 0.0001])
    ch6_latest = np.array([0.0, 0.0001])
    ch7_latest = np.array([0.0, 0.0001])
    ch8_latest = np.array([0.0, 0.0001])
    max_time = 0.0001

    # base pyqtgraph configuration
    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')

    def __init__(self, parent=None):
        self.app = parent

        # lines on a plot
        self.main_plot = self.app.PlotWidget.plotItem
        # configure all eight plots
        two_points = np.array([0.0, 0.0001], dtype="float32")
        self.plot_ch1 = self.main_plot.plot(two_points, two_points, pen=pg.mkPen('#a6cee3', width=3))
        self.app.ch1_chkbox.setStyleSheet("color : #a6cee3;")
        self.plot_ch2 = self.main_plot.plot(two_points, two_points, pen=pg.mkPen('#1f78b4', width=3))
        self.app.ch2_chkbox.setStyleSheet("color : #1f78b4;")
        self.plot_ch3 = self.main_plot.plot(two_points, two_points, pen=pg.mkPen('#b2df8a', width=3))
        self.app.ch3_chkbox.setStyleSheet("color : #b2df8a;")
        self.plot_ch4 = self.main_plot.plot(two_points, two_points, pen=pg.mkPen('#33a02c', width=3))
        self.app.ch4_chkbox.setStyleSheet("color : #33a02c;")
        self.plot_ch5 = self.main_plot.plot(two_points, two_points, pen=pg.mkPen('#fb9a99', width=3))
        self.app.ch5_chkbox.setStyleSheet("color : #fb9a99;")
        self.plot_ch6 = self.main_plot.plot(two_points, two_points, pen=pg.mkPen('#e31a1c', width=3))
        self.app.ch6_chkbox.setStyleSheet("color : #e31a1c;")
        self.plot_ch7 = self.main_plot.plot(two_points, two_points, pen=pg.mkPen('#fdbf6f', width=3))
        self.app.ch7_chkbox.setStyleSheet("color : #fdbf6f;")
        self.plot_ch8 = self.main_plot.plot(two_points, two_points, pen=pg.mkPen('#ff7f00', width=3))
        self.app.ch8_chkbox.setStyleSheet("color : #ff7f00;")
        # '#cab2d6' '#6a3d9a' '#ffff99' '#b15928'
        # initially hide them all
        self.plot_ch1.hide()
        self.plot_ch2.hide()
        self.plot_ch3.hide()
        self.plot_ch4.hide()
        self.plot_ch5.hide()
        self.plot_ch6.hide()
        self.plot_ch7.hide()
        self.plot_ch8.hide()
        self.main_plot.showGrid(True, True)
        # disable auto range initially
        self.main_plot.disableAutoRange()

        self.main_plot.vb.autoRange(items=[self.plot_ch1, self.plot_ch2, self.plot_ch3, self.plot_ch4,
                                           self.plot_ch5, self.plot_ch6, self.plot_ch7, self.plot_ch8])
        self.mouse_point = QtCore.QPoint(0, 0)


        # Add crosshair lines with text
        self.max_time = 0.0001

        self.crosshair_v = pg.InfiniteLine(angle=90, pen='r', movable=False)
        self.crosshair_h = pg.InfiniteLine(angle=0, pen='r', movable=False)
        self.main_plot.addItem(self.crosshair_v, ignoreBounds=True)
        self.main_plot.addItem(self.crosshair_h, ignoreBounds=True)
        self.crosshair_v.hide()
        self.crosshair_h.hide()

        self.crosshair_text = pg.TextItem("0.0, 0.0", color='r', anchor=(0, 0))
        self.main_plot.addItem(self.crosshair_text)
        self.crosshair_text.hide()
        self.proxy = pg.SignalProxy(self.main_plot.scene().sigMouseMoved, rateLimit=60, slot=self.update_crosshair)

        self.app.commonitor.connect_rx_handler(0x0901, self.on_received_ch1)
        self.app.commonitor.connect_rx_handler(0x0902, self.on_received_ch2)
        self.app.commonitor.connect_rx_handler(0x0903, self.on_received_ch3)
        self.app.commonitor.connect_rx_handler(0x0904, self.on_received_ch4)
        self.app.commonitor.connect_rx_handler(0x0905, self.on_received_ch5)
        self.app.commonitor.connect_rx_handler(0x0906, self.on_received_ch6)
        self.app.commonitor.connect_rx_handler(0x0907, self.on_received_ch7)
        self.app.commonitor.connect_rx_handler(0x0908, self.on_received_ch8)

        self.app.commonitor.connect_rx_handler(0x090A, self.on_dlog_params_received)

        # connect chanel select checkbox
        self.app.ch1_chkbox.stateChanged.connect(self.ch1_state_changed)
        self.app.ch2_chkbox.stateChanged.connect(self.ch2_state_changed)
        self.app.ch3_chkbox.stateChanged.connect(self.ch3_state_changed)
        self.app.ch4_chkbox.stateChanged.connect(self.ch4_state_changed)
        self.app.ch5_chkbox.stateChanged.connect(self.ch5_state_changed)
        self.app.ch6_chkbox.stateChanged.connect(self.ch6_state_changed)
        self.app.ch7_chkbox.stateChanged.connect(self.ch7_state_changed)
        self.app.ch8_chkbox.stateChanged.connect(self.ch8_state_changed)

        self.app.cb_cursor.stateChanged.connect(self.cb_cursor_clicked)

        # connect dlog items
        self.app.points_spin.setOpts(value=200, dec=True, step=1, minStep=1, int=True)
        self.app.points_spin.setMinimum(10)
        self.app.points_spin.setMaximum(1000)
        self.app.points_spin.valueChanged.connect(self.points_changed)
        self.app.prescalar_spin.setOpts(value=1, dec=True, step=1, minStep=1, int=True)
        self.app.prescalar_spin.setMinimum(1)
        self.app.prescalar_spin.setMaximum(100)
        self.app.prescalar_spin.valueChanged.connect(self.prescaler_changed)
        self.app.trigger.currentIndexChanged.connect(self.trigger_changed)

        self.samp_freq = 20000

        # zahtevam statusne podatke za data logger in generator signalov
        # if com port is open request parameters
        if self.app.commonitor.is_port_open():
            self.app.commonitor.send_packet(0x092A, None)
        else:
            self.app.commonitor.register_on_open_callback(self.req_dlog_params)

    def cb_cursor_clicked(self):
        if self.app.cb_cursor.isChecked():
            self.crosshair_v.show()
            self.crosshair_h.show()
            self.crosshair_text.show()
        else:
            self.crosshair_v.hide()
            self.crosshair_h.hide()
            self.crosshair_text.hide()

    def update_crosshair(self, e):
        if self.app.cb_cursor.isChecked():
            pos = e[0]
            if self.main_plot.sceneBoundingRect().contains(pos):
                mouse_point = self.main_plot.vb.mapSceneToView(pos)
                view_range = self.main_plot.vb.viewRange()
                # the cursor should stay within data range to avoid panning
                point_x = mouse_point.x()
                cursor = QtCore.Qt.CursorShape.BlankCursor
                if mouse_point.x() < 0:
                    point_x = 0
                    cursor = QtCore.Qt.CursorShape.ArrowCursor
                if mouse_point.x() > self.max_time:
                    point_x = self.max_time
                    cursor = QtCore.Qt.CursorShape.ArrowCursor

                point_y = mouse_point.y()
                if mouse_point.y() < view_range[1][0]:
                    point_y = view_range[1][0]
                    cursor = QtCore.Qt.CursorShape.ArrowCursor
                if mouse_point.y() > view_range[1][1]:
                    point_y = view_range[1][1]
                    cursor = QtCore.Qt.CursorShape.ArrowCursor

                self.main_plot.setCursor(cursor)

                x = eng_string(point_x, format='%.2f', si=True)
                y = eng_string(point_y, format='%.2f', si=True)

                self.crosshair_v.setPos(point_x)
                self.crosshair_h.setPos(point_y)
                self.crosshair_text.setText(x+","+y)
                self.crosshair_text.setPos(point_x, point_y)

    def on_received_ch1(self):
        # potegnem ven podatke direktno v np.array
        self.ch1_latest = np.frombuffer(self.app.commonitor.get_data(), dtype=np.float32)
        # in klicem izris grafa ce je treba izrisati samo ch1
        if (self.app.ch1_chkbox.isChecked() and
                not self.app.ch2_chkbox.isChecked() and
                not self.app.ch3_chkbox.isChecked() and
                not self.app.ch4_chkbox.isChecked() and
                not self.app.ch5_chkbox.isChecked() and
                not self.app.ch6_chkbox.isChecked() and
                not self.app.ch7_chkbox.isChecked() and
                not self.app.ch8_chkbox.isChecked()):
            self.draw_plot()

    def on_received_ch2(self):
        # potegnem ven podatke direktno v np.array
        self.ch2_latest = np.frombuffer(self.app.commonitor.get_data(), dtype=np.float32)
        # in klicem izris grafa ce je treba izrisati samo ch2
        if (self.app.ch2_chkbox.isChecked() and
                not self.app.ch3_chkbox.isChecked() and
                not self.app.ch4_chkbox.isChecked() and
                not self.app.ch5_chkbox.isChecked() and
                not self.app.ch6_chkbox.isChecked() and
                not self.app.ch7_chkbox.isChecked() and
                not self.app.ch8_chkbox.isChecked()):
            self.draw_plot()

    def on_received_ch3(self):
        # potegnem ven podatke direktno v np.array
        self.ch3_latest = np.frombuffer(self.app.commonitor.get_data(), dtype=np.float32)
        # in klicem izris grafa ce je treba izrisati samo ch3
        if (self.app.ch3_chkbox.isChecked() and
                not self.app.ch4_chkbox.isChecked() and
                not self.app.ch5_chkbox.isChecked() and
                not self.app.ch6_chkbox.isChecked() and
                not self.app.ch7_chkbox.isChecked() and
                not self.app.ch8_chkbox.isChecked()):
            self.draw_plot()

    def on_received_ch4(self):
        # potegnem ven podatke direktno v np.array
        self.ch4_latest = np.frombuffer(self.app.commonitor.get_data(), dtype=np.float32)
        # in klicem izris grafa ce je treba izrisati samo ch4
        if (self.app.ch4_chkbox.isChecked() and
                not self.app.ch5_chkbox.isChecked() and
                not self.app.ch6_chkbox.isChecked() and
                not self.app.ch7_chkbox.isChecked() and
                not self.app.ch8_chkbox.isChecked()):
            self.draw_plot()

    def on_received_ch5(self):
        # potegnem ven podatke direktno v np.array
        self.ch5_latest = np.frombuffer(self.app.commonitor.get_data(), dtype=np.float32)
        # in klicem izris grafa ce je treba izrisati samo ch5
        if (self.app.ch5_chkbox.isChecked() and
                not self.app.ch6_chkbox.isChecked() and
                not self.app.ch7_chkbox.isChecked() and
                not self.app.ch8_chkbox.isChecked()):
            self.draw_plot()

    def on_received_ch6(self):
        # potegnem ven podatke direktno v np.array
        self.ch6_latest = np.frombuffer(self.app.commonitor.get_data(), dtype=np.float32)
        # in klicem izris grafa ce je treba izrisati samo ch6
        if (self.app.ch6_chkbox.isChecked() and
                not self.app.ch7_chkbox.isChecked() and
                not self.app.ch8_chkbox.isChecked()):
            self.draw_plot()

    def on_received_ch7(self):
        # potegnem ven podatke direktno v np.array
        self.ch7_latest = np.frombuffer(self.app.commonitor.get_data(), dtype=np.float32)
        # in klicem izris grafa ce je treba izrisati samo ch7
        if (self.app.ch7_chkbox.isChecked() and
                not self.app.ch8_chkbox.isChecked()):
            self.draw_plot()

    def on_received_ch8(self):
        # potegnem ven podatke direktno v np.array
        self.ch8_latest = np.frombuffer(self.app.commonitor.get_data(), dtype=np.float32)
        # in klicem izris grafa ce je treba izrisati samo ch1
        if self.app.ch8_chkbox.isChecked():
            self.draw_plot()

    def draw_plot(self):
        # naracunam x os
        dt = 1.0 / self.samp_freq
        time = np.arange(0, self.app.points_spin.value(), dtype=np.float32) * dt
        self.max_time = time[-1]

        # graf narisem samo ce sem v normal ali signle mode nacinu
        if self.app.trigger_mode.currentText() == "Normal" or self.app.trigger_mode.currentText() == "Single":
            if self.app.ch1_chkbox.isChecked():
                if self.ch1_latest.size == time.size:
                    self.plot_ch1.setData(time, self.ch1_latest)
            if self.app.ch2_chkbox.isChecked():
                if self.ch2_latest.size == time.size:
                    self.plot_ch2.setData(time, self.ch2_latest)
            if self.app.ch3_chkbox.isChecked():
                if self.ch3_latest.size == time.size:
                    self.plot_ch3.setData(time, self.ch3_latest)
            if self.app.ch4_chkbox.isChecked():
                if self.ch4_latest.size == time.size:
                    self.plot_ch4.setData(time, self.ch4_latest)
            if self.app.ch5_chkbox.isChecked():
                if self.ch5_latest.size == time.size:
                    self.plot_ch5.setData(time, self.ch5_latest)
            if self.app.ch6_chkbox.isChecked():
                if self.ch6_latest.size == time.size:
                    self.plot_ch6.setData(time, self.ch6_latest)
            if self.app.ch7_chkbox.isChecked():
                if self.ch7_latest.size == time.size:
                    self.plot_ch7.setData(time, self.ch7_latest)
            if self.app.ch8_chkbox.isChecked():
                if self.ch8_latest.size == time.size:
                    self.plot_ch8.setData(time, self.ch8_latest)

            # ce sem v single mode nacinu potem grem v stop mode
            if self.app.trigger_mode.currentText() == "Single":
                self.app.trigger_mode.blockSignals(True)
                self.app.trigger_mode.setCurrentIndex(2)
                self.app.trigger_mode.blockSignals(False)

    def on_dlog_params_received(self):
        # potegnem ven podatke
        data = self.app.commonitor.get_data()

        # sedaj pa odkodiram podatke
        send_ch1 = struct.unpack('<h', data[0:2])[0]
        send_ch2 = struct.unpack('<h', data[2:4])[0]
        send_ch3 = struct.unpack('<h', data[4:6])[0]
        send_ch4 = struct.unpack('<h', data[6:8])[0]
        send_ch5 = struct.unpack('<h', data[8:10])[0]
        send_ch6 = struct.unpack('<h', data[10:12])[0]
        send_ch7 = struct.unpack('<h', data[12:14])[0]
        send_ch8 = struct.unpack('<h', data[14:16])[0]
        points = struct.unpack('<h', data[16:18])[0]
        prescalar = struct.unpack('<h', data[18:20])[0]
        sampling_freq = struct.unpack('<i', data[20:24])[0]
        trigger = struct.unpack('<h', data[24:26])[0]

        self.samp_freq = sampling_freq/prescalar
        self.app.lbl_samp_freq.setText(str(int(self.samp_freq)))

        # ustrezno nastavim GUI elemente
        self.app.points_spin.blockSignals(True)
        self.app.points_spin.setValue(points)
        self.app.points_spin.blockSignals(False)

        self.app.prescalar_spin.blockSignals(True)
        self.app.prescalar_spin.setValue(prescalar)
        self.app.prescalar_spin.blockSignals(False)

        self.app.ch1_chkbox.blockSignals(True)
        if send_ch1 != 0:
            self.app.ch1_chkbox.setChecked(True)
            self.plot_ch1.show()
        else:
            self.app.ch1_chkbox.setChecked(False)
            self.plot_ch1.hide()
        self.app.ch1_chkbox.blockSignals(False)

        self.app.ch2_chkbox.blockSignals(True)
        if send_ch2 != 0:
            self.app.ch2_chkbox.setChecked(True)
            self.plot_ch2.show()
        else:
            self.app.ch2_chkbox.setChecked(False)
            self.plot_ch2.hide()
        self.app.ch2_chkbox.blockSignals(False)

        self.app.ch3_chkbox.blockSignals(True)
        if send_ch3 != 0:
            self.app.ch3_chkbox.setChecked(True)
            self.plot_ch3.show()
        else:
            self.app.ch3_chkbox.setChecked(False)
            self.plot_ch3.hide()
        self.app.ch3_chkbox.blockSignals(False)

        self.app.ch4_chkbox.blockSignals(True)
        if send_ch4 != 0:
            self.app.ch4_chkbox.setChecked(True)
            self.plot_ch4.show()
        else:
            self.app.ch4_chkbox.setChecked(False)
            self.plot_ch4.hide()
        self.app.ch4_chkbox.blockSignals(False)

        self.app.ch5_chkbox.blockSignals(True)
        if send_ch5 != 0:
            self.app.ch5_chkbox.setChecked(True)
            self.plot_ch5.show()
        else:
            self.app.ch5_chkbox.setChecked(False)
            self.plot_ch5.hide()
        self.app.ch5_chkbox.blockSignals(False)

        self.app.ch6_chkbox.blockSignals(True)
        if send_ch6 != 0:
            self.app.ch6_chkbox.setChecked(True)
            self.plot_ch6.show()
        else:
            self.app.ch6_chkbox.setChecked(False)
            self.plot_ch6.hide()
        self.app.ch6_chkbox.blockSignals(False)

        self.app.ch7_chkbox.blockSignals(True)
        if send_ch7 != 0:
            self.app.ch7_chkbox.setChecked(True)
            self.plot_ch7.show()
        else:
            self.app.ch7_chkbox.setChecked(False)
            self.plot_ch7.hide()
        self.app.ch7_chkbox.blockSignals(False)

        self.app.ch8_chkbox.blockSignals(True)
        if send_ch8 != 0:
            self.app.ch8_chkbox.setChecked(True)
            self.plot_ch8.show()
        else:
            self.app.ch8_chkbox.setChecked(False)
            self.plot_ch8.hide()
        self.app.ch8_chkbox.blockSignals(False)

        if (self.app.ch1_chkbox.isChecked() and self.app.ch2_chkbox.isChecked() and
                self.app.ch3_chkbox.isChecked() and self.app.ch4_chkbox.isChecked() and
                self.app.ch5_chkbox.isChecked() and self.app.ch6_chkbox.isChecked() and
                self.app.ch7_chkbox.isChecked() and self.app.ch8_chkbox.isChecked()):
            self.main_plot.disableAutoRange()
        else:
            self.main_plot.enableAutoRange()

        self.app.trigger.blockSignals(True)
        self.app.trigger.setCurrentIndex(trigger)
        self.app.trigger.blockSignals(False)

    # ob spremembi prescalerja
    def prescaler_changed(self):
        # posljem paket po portu
        data = struct.pack('<h', self.app.prescalar_spin.value())
        self.app.commonitor.send_packet(0x0920, data)
        # zahtevaj se povratni odgovor
        self.app.commonitor.send_packet(0x092A, None)

    # ob spremembi stevila tock
    def points_changed(self):
        # posljem paket po portu
        data = struct.pack('<h', int(self.app.points_spin.value()))
        self.app.commonitor.send_packet(0x0921, data)
        # zahtevaj se povratni odgovor
        self.app.commonitor.send_packet(0x092A, None)

    # ob spremembi triggerja
    def trigger_changed(self):
        # posljem paket po portu
        self.app.commonitor.send_packet(0x0922, struct.pack('<h', self.app.trigger.currentIndex()))
        # zahtevaj se povratni odgovor
        self.app.commonitor.send_packet(0x092A, None)

    # ob pritisku na ch 1
    def ch1_state_changed(self):
        if self.app.ch1_chkbox.isChecked():
            self.app.commonitor.send_packet(0x0911, struct.pack('<h', 0x0001))
        else:
            self.app.commonitor.send_packet(0x0911, struct.pack('<h', 0x0000))
        # zahtevaj se povratni odgovor
        self.app.commonitor.send_packet(0x092A, None)

    # ob pritisku na ch 2
    def ch2_state_changed(self):
        if self.app.ch2_chkbox.isChecked():
            self.app.commonitor.send_packet(0x0912, struct.pack('<h', 0x0001))
        else:
            self.app.commonitor.send_packet(0x0912, struct.pack('<h', 0x0000))
        # zahtevaj se povratni odgovor
        self.app.commonitor.send_packet(0x092A, None)

    # ob pritisku na ch 3
    def ch3_state_changed(self):
        if self.app.ch3_chkbox.isChecked():
            self.app.commonitor.send_packet(0x0913, struct.pack('<h', 0x0001))
        else:
            self.app.commonitor.send_packet(0x0913, struct.pack('<h', 0x0000))
        # zahtevaj se povratni odgovor
        self.app.commonitor.send_packet(0x092A, None)

    # ob pritisku na ch 4
    def ch4_state_changed(self):
        if self.app.ch4_chkbox.isChecked():
            self.app.commonitor.send_packet(0x0914, struct.pack('<h', 0x0001))
        else:
            self.app.commonitor.send_packet(0x0914, struct.pack('<h', 0x0000))
        # zahtevaj se povratni odgovor
        self.app.commonitor.send_packet(0x092A, None)

    # ob pritisku na ch 5
    def ch5_state_changed(self):
        if self.app.ch5_chkbox.isChecked():
            self.app.commonitor.send_packet(0x0915, struct.pack('<h', 0x0001))
        else:
            self.app.commonitor.send_packet(0x0915, struct.pack('<h', 0x0000))
        # zahtevaj se povratni odgovor
        self.app.commonitor.send_packet(0x092A, None)

    # ob pritisku na ch 6
    def ch6_state_changed(self):
        if self.app.ch6_chkbox.isChecked():
            self.app.commonitor.send_packet(0x0916, struct.pack('<h', 0x0001))
        else:
            self.app.commonitor.send_packet(0x0916, struct.pack('<h', 0x0000))
        # zahtevaj se povratni odgovor
        self.app.commonitor.send_packet(0x092A, None)

    # ob pritisku na ch 7
    def ch7_state_changed(self):
        if self.app.ch7_chkbox.isChecked():
            self.app.commonitor.send_packet(0x0917, struct.pack('<h', 0x0001))
        else:
            self.app.commonitor.send_packet(0x0917, struct.pack('<h', 0x0000))
        # zahtevaj se povratni odgovor
        self.app.commonitor.send_packet(0x092A, None)

    # ob pritisku na ch 8
    def ch8_state_changed(self):
        if self.app.ch8_chkbox.isChecked():
            self.app.commonitor.send_packet(0x0918, struct.pack('<h', 0x0001))
        else:
            self.app.commonitor.send_packet(0x0918, struct.pack('<h', 0x0000))
        # zahtevaj se povratni odgovor
        self.app.commonitor.send_packet(0x092A, None)

    def req_dlog_params(self):
        self.app.commonitor.send_packet(0x092A, None)

def eng_string(x, format='%s', si=False):
    """
    Returns float/int value <x> formatted in a simplified engineering format -
    using an exponent that is a multiple of 3.

    format: printf-style string used to format the value before the exponent.

    si: if true, use SI suffix for exponent, e.g. k instead of e3, n instead of
    e-9 etc.

    E.g. with format='%.2f':
        1.23e-08 => 12.30e-9
             123 => 123.00
          1230.0 => 1.23e3
      -1230000.0 => -1.23e6

    and with si=True:
          1230.0 => 1.23k
      -1230000.0 => -1.23M
    """
    sign = ''
    x = float(x)
    if x < 0:
        x = -x
        sign = '-'
    if x == 0.0:
        exp = 0
    else:
        exp = int(math.floor(math.log10(x)))
    exp3 = exp - (exp % 3)
    x3 = x / (10 ** exp3)

    if si and exp3 >= -24 and exp3 <= 24 and exp3 != 0:
        index_f = ( exp3 - (-24)) / 3
        index = int(index_f)
        exp3_text = 'yzafpnum kMGTPEZY'[index]
    elif exp3 == 0:
        exp3_text = ''
    else:
        exp3_text = 'e%s' % exp3

    return ('%s'+format+'%s') % (sign, x3, exp3_text)
