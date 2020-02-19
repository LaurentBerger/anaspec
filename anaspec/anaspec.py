#!/usr/bin/env python3
"""Plot the live microphone signal(s) with matplotlib.

Matplotlib and NumPy have to be installed.

"""
import argparse
import queue
import sys
import time

from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
import numpy as np
import sounddevice as sd
import wx
import wx.lib.agw.aui as aui
import wx.lib.newevent

import base_button4 as bb


class Plot(wx.Panel):
    def __init__(self, parent, id=-1, dpi=None, **kwargs):
        wx.Panel.__init__(self, parent, id=id, **kwargs)
        self.parent = parent
        self.figure, self.ax = plt.subplots()
        self.lines = self.ax.plot(plotdata)
        self.ax.legend(['channel {}'.format(c) for c in range(nb_canaux)],
                    loc='lower left', ncol=nb_canaux)
        self.ax.axis((0, len(plotdata)/2, -1, 1))
        self.ax.yaxis.grid(True)
        self.figure.tight_layout(pad=0)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        self.SetSizer(sizer)
        
    def DrawPage(self,evt):
        self.update_plot(None)
        return 

    def update_plot(self, frame):
        """This is called by matplotlib for each plot update.

        Typically, audio callbacks happen more frequently than plot updates,
        therefore the queue tends to contain multiple blocks of audio data.

        """
        global plotdata
        while True:
            try:
                data = q.get_nowait()
            except queue.Empty:
                break
            shift = len(data)
            plotdata = np.roll(plotdata, -shift, axis=0)
            plotdata[-shift:, :] = data
        for column, line in enumerate(self.lines):
            line.set_ydata((column+1) *plotdata[:, column])
        return self.lines


class PlotNotebook(wx.Panel):
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id=id)
        self.nb = aui.AuiNotebook(self)
        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        self.page = []
        self.SetSizer(sizer)
        self.parent =  parent
        self.Bind(EVT_SOME_NEW_EVENT, self.drawPage)
        self.clock = 0

    def add(self, name="plot"):
        page =  Plot(self.nb)
        self.page.append(page)
        self.nb.AddPage(page, name)
        return page

    def drawPage(self, evt):
        if time.clock() - self.clock <0.10:
            return 
        self.clock = time.clock()
        for page in self.page:
            if self.nb.GetCurrentPage() == page:
                page.DrawPage(evt)
                page.canvas.draw()

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text



def audio_callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    # Fancy indexing with mapping creates a (necessary!) copy:
    q.put(indata[::nb_elt_affiche, mapping])
    # Create the event
    evt = SomeNewEvent(attr1="hello", attr2=654)
    # Post the event
    wx.PostEvent(plotter, evt)



try:
    nb_ech_fenetre = 2048
    nb_elt_affiche = 1
    nb_canaux = 2
    tps_refresh = 30
    Fe = 44100
    length = int(nb_ech_fenetre )
    plotdata = np.zeros((length, nb_canaux))
    mapping = [c-1  for c in range(nb_canaux)]  # Channel numbers start with 1
    q = queue.Queue()

    app = wx.App()

    SomeNewEvent, EVT_SOME_NEW_EVENT = wx.lib.newevent.NewEvent()
    SomeNewCommandEvent, EVT_SOME_NEW_COMMAND_EVENT = wx.lib.newevent.NewCommandEvent()

    frame = wx.Frame(None, -1, 'Mes Courbes')
    plotter = PlotNotebook(frame)
    page1 = plotter.add('figure 1')
    frame.Show()
    print(sd.query_devices())
    device = None
    device_info = sd.query_devices(None, 'input')
    Fe = device_info['default_samplerate']
    frame = bb.MaFenetre()

    stream = sd.InputStream(
        device=None, channels=nb_canaux-1,
        samplerate=Fe, callback=audio_callback)
    

    with stream:
        app.MainLoop()
except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))
