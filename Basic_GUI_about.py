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

        # register button click
        self.btn_ok.clicked.connect(self.ok_click)

        # check if git_commit_sha.txt file exist
        # if it doesn't exist, create it
        if not os.path.exists('git_commit_sha.txt'):
            with open('git_commit_sha.txt', 'w') as f:
                f.write('NoCommit\n')
        with open('git_commit_sha.txt') as f:
            sha = f.readline().strip()
        self.lbl_git_sha.setText("Git SHA: "+sha)

    # ce pritisnem OK potem zaprem okno
    def ok_click(self):
        self.close()
