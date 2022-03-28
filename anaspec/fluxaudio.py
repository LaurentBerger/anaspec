import queue
import sys

import numpy as np
import sounddevice as sd
import wx
import wx.lib.newevent

NEW_EVENT = None
# flux_audio variable global utilisée dans callback  audio_callback
FLUX_AUDIO = None
NB_BUFFER = 64

class FluxAudio:
    """
    flux audio et ensemble des paramètres associés
    """
    def __init__(self, n_evt, freq=44100, fenetre=2048, canaux=2):
        global NEW_EVENT
        global FLUX_AUDIO
        FLUX_AUDIO = self
        NEW_EVENT = n_evt
        self.nb_buffer = 64
        self.ind_buffer = 0
        self.nb_ech_fenetre = fenetre
        self.nb_canaux = canaux
        self.tps_refresh = 0.1
        self.Fe = freq
        self.courbe = None
        self.file_attente = queue.Queue()
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
        return sd.query_devices()

    def set_k_min(self, idx_min):
        idx_min = int(idx_min / self.Fe * self.nb_ech_fenetre)
        if idx_min < self.k_max:
            self.k_min = idx_min

    def set_k_max(self, idx_max):
        idx_max = int(idx_max / self.Fe * self.nb_ech_fenetre)
        if idx_max > self.k_min:
            self.k_max = idx_max

    def set_f_min_spectro(self, f_min):
        if f_min < self.f_max_spectro:
            self.f_min_spectro = f_min

    def set_f_max_spectro(self, f_max):
        if f_max > self.f_min_spectro:
            self.f_max_spectro = f_max

    def set_win_size_spectro(self ,taille):
        self.win_size_spectro = taille

    def set_overlap_spectro(self, recou):
        self.overlap_spectro = recou

    def init_data_courbe(self):
        length = int(self.nb_ech_fenetre)
        self.plotdata = np.zeros((self.nb_buffer * length, self.nb_canaux))
        self.mapping = [c-1  for c in range(self.nb_canaux)]  # Channel numbers start with 1

    def set_frequency(self, freq_ech):
        self.Fe = freq_ech

    def set_window_size(self, nb_ech):
        self.nb_ech_fenetre = nb_ech

    def set_time_length(self, _):
        self.duration = -1


    def open(self, device_idx):
        self.init_data_courbe()
        print(device_idx)

        self.stream = sd.InputStream(
            device=device_idx, channels=self.nb_canaux-1,
            samplerate=self.Fe, callback=audio_callback)
        self.stream.start()
        return True

    def close(self):
        self.stream.stop()
        self.stream.close()

def audio_callback(indata, _frames, _time, status):
    """Fonction appelée lorsque des données audio sont disponibles."""
    if status:
        print(status, file=sys.stderr)
    # Copie des données dans la file:
    FLUX_AUDIO.file_attente.put(indata[:, FLUX_AUDIO.mapping])
    if FLUX_AUDIO.courbe.evt_process:
        # Création d'un événement
        FLUX_AUDIO.courbe.evt_process = False
        evt = NEW_EVENT(attr1="audio_callback", attr2=0)
        # Envoi de l'événement à la fenêtre chargée du tracé
        wx.PostEvent(FLUX_AUDIO.courbe, evt)
