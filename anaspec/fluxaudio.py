from pickle import NONE
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

frequence_num = [11025.0, 22050.0, 44100.0, 48000.0, 88200.0, 176400.0]


class FluxAudio:
    """
    flux audio et ensemble des paramètres associés
    """
    def __init__(self, n_evt, freq=44100, fenetre=2048, canaux=1):
        global NEW_EVENT
        global FLUX_AUDIO
        FLUX_AUDIO = self
        NEW_EVENT = n_evt
        self.taille_buffer_signal = int(3*max(frequence_num))
        self.nb_ech_fenetre = fenetre # pour l'acquisition
        self.tfd_size = self.nb_ech_fenetre
        self.spectro_size = self.nb_ech_fenetre
        self.nb_canaux = canaux
        self.nb_data = 0
        self.tps_refresh = 0.1
        self.Fe = freq
        self.courbe = None
        self.file_attente = queue.Queue()
        self.stream = None
        self.duration = -1
        self.plotdata = None
        self.mapping = None
        self.k_min = 0
        self.k_max = self.tfd_size//2+1
        self.f_min_spectro = 0
        self.f_max_spectro = self.Fe // 2
        self.win_size_spectro = self.spectro_size // 2
        self.overlap_spectro = self.spectro_size // 16
        self.type_fenetre = ('boxcar')
        self.simulate =  False
        self.frequence_dispo =  [] # frequence possible sur le périphérique
        self.max_canaux =  0 # nombre maximum de canaux disponiobles pour la numérisation

    def get_device(self):
        return sd.query_devices()

    def set_tfd_size(self, val=None):
        if val is not None:
            self.tfd_size = val
        return self.tfd_size

    def set_k_min(self, idx_min):
        idx_min = int(idx_min / self.Fe * self.tfd_size)
        if idx_min < self.k_max:
            self.k_min = idx_min

    def set_k_max(self, idx_max):
        idx_max = int(idx_max / self.Fe * self.tfd_size)
        if idx_max > self.k_min:
            self.k_max = idx_max

    def set_spectro_size(self, val):
        if val is not NONE:
            self.spectro_size = val
        return self.spectro_size

    def set_f_min_spectro(self, f_min):
        if f_min < self.f_max_spectro:
            self.f_min_spectro = f_min

    def set_f_max_spectro(self, f_max):
        if f_max > self.f_min_spectro:
            self.f_max_spectro = f_max

    def set_win_size_spectro(self, taille):
        self.win_size_spectro = taille

    def set_overlap_spectro(self, recou):
        self.overlap_spectro = recou

    def init_data_courbe(self):
        self.plotdata = np.ones((self.taille_buffer_signal, self.nb_canaux))
        self.mapping = [c-1 for c in range(self.nb_canaux)]

    def set_frequency(self, freq_ech):
        self.Fe = freq_ech

    def set_window_size(self, nb_ech):
        self.nb_ech_fenetre = nb_ech

    def set_time_length(self, _):
        self.duration = -1
    
    def capacite_periph_in(self, liste_periph, device_idx):
        self.frequence_dispo = set({})
        self.frequence_dispo.update([str(liste_periph[device_idx]['default_samplerate'])])
        self.max_canaux = liste_periph[device_idx]['max_input_channels']
        self.nb_canaux = self.max_canaux
        for freq in frequence_num:
            try:
                self.stream = sd.InputStream(
                    device=device_idx, channels=self.nb_canaux,
                    samplerate=freq, callback=audio_callback)
                self.stream.start()
                self.stream.close()
                self.frequence_dispo.update([str(freq)])
            except:
                pass
        print(self.frequence_dispo)


    def open(self, device_idx):
        self.init_data_courbe()
        self.file_attente = queue.Queue()
        self.stream = sd.InputStream(
            device=device_idx, channels=self.nb_canaux,
            samplerate=self.Fe, callback=audio_callback)
        self.nb_data = 0
        self.stream.start()
        return True

    def close(self):
        self.stream.stop()
        self.stream.close()

    def new_sample(self):
        """ Réception de nouvelle données
        du signal audio
        """
        while True:
            try:
                # https://docs.python.org/3/library/queue.html#queue.Queue.get_nowait
                data = self.file_attente.get_nowait()
            except queue.Empty:
                break

            shift = data.shape[0]
            self.nb_data = self.nb_data + shift
            # print("data shape :", data.shape)
            # print("plotdata shape :", self.flux_audio.plotdata.shape)
            if shift < self.plotdata.shape[0]:
                self.plotdata = np.roll(self.plotdata,
                                                   -shift,
                                                   axis=0)
                self.plotdata[-shift:, :] = data
            else:
                raise ValueError("Should not happen")
        return self.nb_data


def audio_callback(indata, _frames, _time, status):
    """Fonction appelée lorsque des données audio sont disponibles."""
    if status:
        print(status, file=sys.stderr)
    # Copie des données dans la file:
    if FLUX_AUDIO.simulate:
        x = np.zeros(shape=indata.shape,dtype=np.float64)
        x[:,0] = np.linspace(0., 0.2, indata.shape[0])
        if x.shape[1] == 2:
            x[:,1] = np.linspace(-0.1, 0.1, indata.shape[0])
        FLUX_AUDIO.file_attente.put(x[:,FLUX_AUDIO.mapping])
    else:
        FLUX_AUDIO.file_attente.put(indata[:,FLUX_AUDIO.mapping])
    # FLUX_AUDIO.file_attente.put(x[:,FLUX_AUDIO.mapping])
    if FLUX_AUDIO.courbe.evt_process:
        # Création d'un événement
        FLUX_AUDIO.courbe.evt_process = False
        evt = NEW_EVENT(attr1="audio_callback", attr2=0)
        # Envoi de l'événement à la fenêtre chargée du tracé
        wx.PostEvent(FLUX_AUDIO.courbe, evt)
