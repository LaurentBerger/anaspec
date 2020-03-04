"""tracé du signale audio en temps réel avec wxmatplotlib.

wx Matplotlib and NumPy have to be installed.

"""
import queue
import sys

import numpy as np
import sounddevice as sd
import wx
import wx.lib.newevent
import interface 



application = wx.App()
frame = wx.Frame(None, -1, 'Mes Courbes')
interface_audio = interface.InterfaceAnalyseur(frame)
frame.Show()
print(sd.query_devices())
device = None

application.MainLoop()
