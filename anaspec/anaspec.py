#!/usr/bin/env python3
"""Plot the live microphone signal(s) with matplotlib.

Matplotlib and NumPy have to be installed.

"""
import queue
import sys
import time

import numpy as np
import sounddevice as sd
import wx
import wx.lib.newevent
import fenetrecourbe as fc

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text
class FluxAudio:
    def __init__(self):
        nb_ech_fenetre = 2048
        nb_elt_affiche = 1
        self.nb_canaux = 2
        tps_refresh = 30
        self.Fe = 44100
        length = int(nb_ech_fenetre )
        self.plotdata = np.zeros((length, nb_canaux))
        mapping = [c-1  for c in range(nb_canaux)]  # Channel numbers start with 1
        self.q = queue.Queue()

    def open(self):
        self.stream = sd.InputStream(
            device=None, channels=self.nb_canaux-1,
            samplerate=self.Fe, callback=audio_callback)

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
    plotter = fc.PlotNotebook(frame, evt_type=EVT_SOME_NEW_EVENT)
    page1 = plotter.add('figure 1')
    frame.Show()
    print(sd.query_devices())
    device = None
    device_info = sd.query_devices(None, 'input')
    Fe = device_info['default_samplerate']

    stream = sd.InputStream(
        device=None, channels=nb_canaux-1,
        samplerate=Fe, callback=audio_callback)
    

    with stream:
        app.MainLoop()
except Exception as e:
    print(type(e).__name__ + ': ' + str(e))
