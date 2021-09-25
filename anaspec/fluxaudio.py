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
    def __init__(self, n_evt, freq=44100, fenetre=2048, canaux=2):
        global new_event
        global flux_audio
        flux_audio = self
        new_event = n_evt
        self.NB_BUFFER = 64
        self.ind_buffer = 0
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
        self.f_min_spectro = 0
        self.f_max_spectro = self.Fe // 2
        self.win_size_spectro = self.nb_ech_fenetre // 2
        self.overlap_spectro = self.nb_ech_fenetre // 16
        self.type_fenetre = ('boxcar')

    def get_device(self):
        s = sd.query_devices()
        return s

    def set_k_min(self, v):
        v = int(v / self.Fe * self.nb_ech_fenetre)
        if v < self.k_max:
            self.k_min = v

    def set_k_max(self, v):
        v = int(v / self.Fe * self.nb_ech_fenetre)
        if v > self.k_min:
            self.k_max = v

    def set_f_min_spectro(self, v):
        if v < self.f_max_spectro:
            self.f_min_spectro = v

    def set_f_max_spectro(self,v):
        if v > self.f_min_spectro:
            self.f_max_spectro = v

    def set_win_size_spectro(self,v):
        self.win_size_spectro = v

    def set_overlap_spectro(self,v):
        self.overlap_spectro = v

    def init_data_courbe(self):
        length = int(self.nb_ech_fenetre)
        self.plotdata = np.zeros((self.NB_BUFFER * length, self.nb_canaux))
        self.mapping = [c-1  for c in range(self.nb_canaux)]  # Channel numbers start with 1

    def set_frequency(self, v):
        self.Fe = freq

    def set_window_size(self, v):
        self.nb_ech_fenetre = fenetre

    def set_time_length(self, v):
        self.duration = -1


    def open(self, device_idx):
        self.init_data_courbe()
        print(device_idx)
        try:

            self.stream = sd.InputStream(
                device=device_idx, channels=self.nb_canaux-1,
                samplerate=self.Fe, callback=audio_callback)
        except Exception as e:
            print(sys.exc_info())
            return False
        self.stream.start()
        return True

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
