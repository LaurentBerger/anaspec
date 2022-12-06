"""tracer du signale audio en temps réel avec wxmatplotlib.

wx Matplotlib and NumPy have to be installed.

"""

import sounddevice as sd
import wx
import wx.lib.newevent
import interface

application = wx.App()
frame = wx.Frame(None, -1, 'Analyser')
interface_audio = interface.InterfaceAnalyseur(frame)
frame.Show()
print(sd.query_devices())

application.MainLoop()
