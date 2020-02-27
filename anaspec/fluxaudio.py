import queue
import sys

import numpy as np
import sounddevice as sd
import wx
import wx.lib.newevent

new_event = None
flux_audio = None

class FluxAudio:
    """
    flux audio et ensemble des paramètres associés
    """
    def __init__(self, n_evt,  freq=44100, fenetre=2048, canaux=2):
        global new_event
        global flux_audio
        flux_audio = self
        new_event = n_evt
        self.nb_ech_fenetre = fenetre
        self.nb_canaux = canaux
        self.tps_refresh = 0.1
        self.Fe = freq
        self.courbe = None
        self.q = queue.Queue()
        self.stream = None
        self.duration = -1
        self.plotdata = None
        self.mapping = None
        self.k_min = 0
        self.k_max = fenetre//2+1

    def init_data_courbe(self):
        length = int(self.nb_ech_fenetre)
        self.plotdata = np.zeros((length, self.nb_canaux))
        self.mapping = [c-1  for c in range(self.nb_canaux)]  # Channel numbers start with 1

    def set_frequency(self, v):
        self.Fe = freq

    def set_window_size(self, v):
        self.nb_ech_fenetre = fenetre

    def set_time_length(self, v):
        self.duration = -1


    def open(self):
        self.init_data_courbe()
        self.stream = sd.InputStream(
            device=None, channels=self.nb_canaux-1,
            samplerate=self.Fe, callback=audio_callback)
        self.stream.start()

    def close(self):
        self.stream.stop()
        self.stream.close()

def audio_callback(indata, _frames, _time, status):
    """Fonction appelée lorsque des données audio sont disponibles."""
    global flux_audio
    if status:
        print(status, file=sys.stderr)
    # Copie des données dans la file:
    flux_audio.q.put(indata[:, flux_audio.mapping])
    if flux_audio.courbe.evt_process:
        # Création d'un événement
        flux_audio.courbe.evt_process = False
        evt = new_event(attr1="audio_callback", attr2=0)
        # Envoi de l'événement à la fenêtre chargée du tracé
        wx.PostEvent(flux_audio.courbe, evt)

