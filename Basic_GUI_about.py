# -*- coding: utf-8 -*-
import Basic_GUI_about_dialog

import os

# Import the PyQt4 module we'll need
from PyQt5 import QtWidgets, QtCore


# About dialog
class About(QtWidgets.QDialog, Basic_GUI_about_dialog.Ui_Dialog):
    def __init__(self, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        # This is defined in GUI_design.py file automatically
        # It sets up layout and widgets that are defined
        self.setupUi(self)

        self.setWindowTitle("About")

        # registriram klik na gumb OK
        self.btn_ok.clicked.connect(self.ok_click)

        # preberem sha
        with open('git_commit_sha.txt') as f:
            sha = f.readline().strip()
        self.lbl_git_sha.setText("Git SHA: "+sha)

    # ce pritisnem OK potem zaprem okno
    def ok_click(self):
        self.close()
