#! /bin/bash

#/usr/local/lib/python3.10/dist-packages/PyQt5/uic/pyuic.py Basic_GUI_COM_settings_dialog.ui -o Basic_GUI_COM_settings_dialog.py
#/usr/local/lib/python3.10/dist-packages/PyQt5/uic/pyuic.py Basic_GUI_COM_statistics_dialog.ui -o Basic_GUI_COM_statistics_dialog.py
#/usr/local/lib/python3.10/dist-packages/PyQt5/uic/pyuic.py Basic_GUI_LOG_mod_dialog.ui -o Basic_GUI_LOG_mod_dialog.py
#/usr/local/lib/python3.10/dist-packages/PyQt5/uic/pyuic.py Basic_GUI_main_window_frame.ui -o Basic_GUI_main_window_frame.py
#/usr/local/lib/python3.10/dist-packages/PyQt5/uic/pyuic.py Basic_GUI_about_dialog.ui -o Basic_GUI_about_dialog.py

for i in *.ui;
do
  pyuic5 "$i" -o "${i/%.ui/.py}"
done

