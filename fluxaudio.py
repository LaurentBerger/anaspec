from pickle import NONE
import queue
import sys

import numpy as np
import sounddevice as sd
import scipy.signal
import wx
import wx.lib.newevent

NEW_EVENT_GEN = None
# flux_audio variable global utilisée dans callback  audio_callback
FLUX_AUDIO = None
NB_BUFFER = 64

frequence_num = [11025.0, 22050.0, 44100.0, 48000.0, 88200.0, 176400.0]

class Signal:
    """
    flux audio et ensemble des paramètres associés
    """
    def __init__(self,freq=44100, fenetre=2048, canaux=1, s_array=None, file_name=None):
        self.nb_ech_fenetre = fenetre # pour l'acquisition
        self.Fe = freq
        if s_array is None:
            self.taille_buffer_signal = int(10*freq)
            self.plotdata = None
        else:
            self.taille_buffer_signal = fenetre
            self.plotdata = s_array
        self.file_name = file_name
        self.nb_ech_fenetre = fenetre # pour l'acquisition
        self.tfd_size = self.nb_ech_fenetre
        self.spectro_size = self.nb_ech_fenetre
        self.f_min = 0 # fréquence minimale sélectionnée
        self.f_max = self.Fe // 2  # fréquence maximale sélectionnée
        self.f_min_spectro = 0
        self.f_max_spectro = self.Fe // 2
        self.k_min = 0 # indice de la fréquence minimale sélectionnée
        self.k_max = self.tfd_size // 2 + 1  # indice de la fréquence maximale sélectionnée
        self.win_size_spectro = self.spectro_size // 2
        self.overlap_spectro = self.spectro_size // 16
        self.nb_canaux = canaux
        self._bp_level = -3
        self._peak_d = 1
        self.set_k_min(self.f_min)
        self.set_k_max(self.f_max)
        self.f_min_spectro = 0
        self.f_max_spectro = self.Fe // 2
        self.type_window = ['boxcar']
        self.fft = None # pour le signal de référence
        self.frequency =  None # pour le signal de référence
        self.spec_selec = None
        self.freq_response = None
        self.offset_synchro = 1 # décalage entre signal et référence

    def set_bp_level(self, val=None):
        if val is not None and -10 <= val <=-1:
            self._bp_level = val
        return self._bp_level

    def set_peak_distance(self, val=None):
        if val is not None and 1<= val <=1000:
            self._peak_d = val
        return self._peak_d

    def set_tfd_size(self, val=None):
        if val is not None:
            self.tfd_size = val
            self.set_k_min(self.set_f_min())
            self.set_k_max(self.set_f_max())
        return self.tfd_size

    def set_k_min(self, idx_min=None):
        if idx_min is not None:
            idx_min = int(idx_min / self.Fe * self.tfd_size)
            if idx_min < self.k_max:
                self.k_min = idx_min
        return self.k_min

    def set_k_max(self, idx_max=None):
        if idx_max is not None:
            idx_max = int(idx_max / self.Fe * self.tfd_size)
            if idx_max > self.k_min:
                self.k_max = idx_max
        return self.k_max

    def set_f_min(self, f_min=None):
        if f_min is not None and 0 <= f_min <= self.Fe/2:
            self.set_k_min(f_min)
            self.f_min = f_min
        return self.f_min

    def set_f_max(self, f_max=None):
        if f_max is not None and 0 <= f_max <= self.Fe/2:
            self.set_k_max(f_max)
            self.f_max = f_max
        return self.f_max

    def set_spectro_size(self, val=None):
        if val is not NONE:
            self.spectro_size = val
        return self.spectro_size

    def set_f_min_spectro(self, f_min=None):
        if f_min is not NONE:
            if f_min < self.f_max_spectro:
                self.f_min_spectro = f_min
        return self.f_min_spectro

    def set_f_max_spectro(self, f_max=None):
        if f_max is not NONE:
            if f_max > self.f_min_spectro:
                self.f_max_spectro = f_max
        return self.f_max_spectro

    def set_win_size_spectro(self, taille=None):
        if taille is not None:
            self.win_size_spectro = taille
        return self.win_size_spectro

    def set_overlap_spectro(self, recou=None):
        if recou is not None:
            self.overlap_spectro = recou
        return self.overlap_spectro

    def compute_spectrum(self):
        self.fft = np.fft.fft(self.plotdata)
        self.frequency =  np.arange(0.0, self.fft.shape[0]//2) * self.Fe / self.fft.shape[0]
        self.spec_selec =  np.abs(self.fft[0: self.fft.shape[0]//2]).real / self.Fe

    def compute_frequency_response(self, signal, threshold=0.1):
        """
        Calcul de la réponse fréquentielle pour
        les fréquences vérifiant que module de 
        la fft > threshold max(fft)
        """
        self.offset_synchro = self.synchroniser(self.plotdata, signal)
        offset_synchro = self.offset_synchro
        if self.offset_synchro>0:
            return False, "Unable to syncronize signal"
        if self.offset_synchro + self.plotdata.shape[0] >= signal.shape[0]:
            return False, "Synchro enable but signal size too small"
        fft_output =  np.fft.fft(signal[-offset_synchro: -offset_synchro + self.plotdata.shape[0]])
        self.freq_response = np.zeros(shape=(self.plotdata.shape[0],1), dtype=np.float64)
        self.freq_response = fft_output / self.fft
        idx = self.fft < self.fft.max() *  threshold
        self.freq_response[idx] = 0.0

    def synchroniser(self, sig1, sig2):
        cxy = scipy.signal.correlate(sig1/sig1.max(), sig2/sig2.max(), method='fft')
        lags = scipy.signal.correlation_lags(len(sig1), len(sig2))
        d = lags[np.argmax(cxy)]
        return d


class FluxAudio(Signal):
    """
    flux audio et ensemble des paramètres associés
    """
    def __init__(self, n_evt=(None,None), freq=44100, fenetre=2048, canaux=1):
        super().__init__(freq, fenetre, canaux)
        global NEW_EVENT_ACQ, NEW_EVENT_GEN
        global FLUX_AUDIO
        FLUX_AUDIO = self
        NEW_EVENT_ACQ = n_evt[0]
        self.NEW_EVENT_GEN = n_evt[1]
        self.file_attente = queue.Queue()
        self.courbe = None
        self.mapping = None
        self.nb_data = 0
        self.simulate =  False
        self.nb_canaux = canaux
        self.Fe = freq
        self.courbe = None
        self.stream = None
        self.duration = -1
        self.tps_refresh = 0.1
        self.frequence_dispo =  [] # frequence possible sur le périphérique
        self.max_canaux =  0 # nombre maximum de canaux disponiobles pour la numérisation
        self.simulate =  False

    def get_device(self):
        return sd.query_devices()

    def get_format_precision(self, val):

        self._decimale =  np.round(np.log10(self.Fe /self.tfd_size))
        self._mantisse = np.round(np.log10(val))
        nb_dig = int(self._mantisse) - int(self._decimale)
        if nb_dig <= 0:
            nb_dig = 1
        self._format =  '.' + str(nb_dig) + 'e'
        return format(val, self._format)


    def init_data_courbe(self):
        self.taille_buffer_signal = int(10 * self.Fe)
        self.plotdata = np.zeros((self.taille_buffer_signal, self.nb_canaux))
        self.mapping = [c-1 for c in range(self.nb_canaux)]

    def set_frequency(self, freq_ech=None):
        if freq_ech != None:
            self.Fe = freq_ech
            self.taille_buffer_signal = int(10 * self.Fe)
            self.plotdata = np.zeros((self.taille_buffer_signal, self.nb_canaux))
            if self.f_min > self.Fe/2:
                self.f_min = self.Fe//2 - 1
            if self.f_max > self.Fe//2:
                self.f_max = self.Fe//2 - 1
        return self.Fe

    def set_window_size(self, nb_ech):
        self.nb_ech_fenetre = nb_ech

    def set_time_length(self, _):
        self.duration = -1
    
    def capacite_periph_in(self, liste_periph, device_idx):
        self.frequence_dispo = []
        self.frequence_dispo.append(str(liste_periph[device_idx]['default_samplerate']))
        self.max_canaux = liste_periph[device_idx]['max_input_channels']
        self.nb_canaux = self.max_canaux
        for freq in frequence_num:
            try:
                self.stream = sd.InputStream(
                    device=device_idx, channels=self.nb_canaux,
                    samplerate=freq, callback=audio_callback)
                self.stream.start()
                self.stream.close()
                if str(freq) not in self.frequence_dispo:
                    self.frequence_dispo.append(str(freq))
            except:
                pass
        print(self.frequence_dispo)


    def open_stream(self, device_idx):
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

    def update_signal_genere(self, son):
        nb_ech = min(son.shape[0], self.plotdata.shape[0])
        t_beg = self.plotdata.shape[0] - nb_ech
        deb = 0
        if t_beg>0:
            deb = t_beg // 2
            t_beg = t_beg - deb
        t_end = self.taille_buffer_signal - deb
        if len(son.shape) == 1:
            self.plotdata[t_beg:t_end,0] = son[:nb_ech]
        else:
            self.flux_audio.plotdata[t_beg:t_end,0] = son[:nb_ech,0]
            if son.shape[1] != self.plotdata.shape[1]:
                wx.MessageBox("Channel number are not equal. First channel uses", "Warning", wx.ICON_WARNING)
            elif son.shape[1] == 2:
                self.plotdata[self.plotdata.shape[0]-nb_ech:,1] += son[:nb_ech,1] 
        evt = self.NEW_EVENT_GEN(attr1=t_beg, attr2=t_end)
        # Envoi de l'événement à la fenêtre chargée du tracé
        wx.PostEvent(FLUX_AUDIO.courbe, evt)


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
