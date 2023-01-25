"""
A DEFINIR

"""

from pickle import NONE
import time
import queue
import threading
from types import NoneType
import numpy as np
from scipy import signal

import matplotlib.pyplot as plt
import matplotlib.patches
import matplotlib.backend_bases
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg\
   as NavigationToolbar

import wx
import wx.lib.newevent
import wx.aui as aui


# pylint: disable=maybe-no-member
EVENT_FFT = None
EVENT_SPECTRO = None
PAGE_PLOT_FFT = None
PAGE_PLOT_SPECTRO = None

SLIDER_T_BEG =8001
SLIDER_T_END =8002

SLIDER_FFT_BEG =8101
SLIDER_FFT_END =8102
BOUTON_COPY_FFT = 8103
BOUTON_NORMALISER = 8104

SLIDER_SPECTRO_BEG =8201
SLIDER_SPECTRO_END =8202
BOUTON_COPY_SPECTRO = 8203
BOUTON_COMPUTE_HZ = 8204

def fast_atan2(y, x):
    if type(y) is not np.ndarray:
        y = np.array([y])
    if type(x) is not np.ndarray:
        x = np.array([x])
    xx = np.abs(x)
    yy = np.abs(y)
    xy = np.array([xx,yy])
    max_xy = np.max(xy, axis=0) 
    idx = np.where(max_xy==0)
    max_xy[idx]=1e-16
    a = np.min(xy, axis=0) / max_xy
    s = a * a
    r = ((-0.0464964749 * s + 0.15931422) * s - 0.327622764) * s * a + a
    idx = np.where(yy > xx)
    r[idx] = 1.57079637 - r[idx]
    idx = np.where(x < 0) 
    r[idx]= 3.14159274 - r[idx]
    idx = np.where(y < 0)
    r[idx] = -r[idx]
    return r



class CalculFFT(threading.Thread):
    """ calcul de la fft en utilisant un thread
    et envoie d'un événement en fin de calcul
    """
    def __init__(self, x, fe, fenetre='boxcar', param=None):
        threading.Thread.__init__(self)
        if fenetre != 'boxcar':
            w = signal.get_window(fenetre, x.shape[0])
            self.x = x.copy() * w
        else:
            self.x = x.copy()
        self.Fe = fe
    
    def run(self):
        self.z = np.fft.fft(self.x)
        self.z = np.abs(self.z).real / self.Fe
        evt = EVENT_FFT(attr1="CalculFFT", attr2=0)
        # Envoi de l'événement à la fenêtre chargée du tracé
        if PAGE_PLOT_FFT:
            PAGE_PLOT_FFT.file_attente.put(self.z.copy())
            wx.PostEvent(PAGE_PLOT_FFT, evt)

class CalculSpectrogram(threading.Thread):
    """ calcul du spectrogramme en utilisant un thread
    et envoie d'un événement en fin de calcul
    """
    def __init__(self, x, fe, win_size_spectro, overlap_spectro, fenetre='boxcar'):
        threading.Thread.__init__(self)
        self.x = x.copy()
        self.Fe = fe
        self.win_size_spectro = win_size_spectro
        self.overlap_spectro = overlap_spectro
        self.type_fenetre = fenetre
    
    def run(self):
        _, _, self.z = signal.spectrogram(
                self.x,
                self.Fe,
                nperseg=self.win_size_spectro,
                noverlap=self.overlap_spectro,
                window=tuple([self.type_fenetre]))
        evt = EVENT_SPECTRO(attr1="CalculSpectrogram", attr2=0)
        # Envoi de l'événement à la fenêtre chargée du tracé
        if PAGE_PLOT_SPECTRO:
            PAGE_PLOT_SPECTRO.file_attente.put(self.z.copy())
            wx.PostEvent(PAGE_PLOT_SPECTRO, evt)


class Plot(wx.Panel):
    """
    Fenetrage wx contenant un graphique matplotlib
    """
    def __init__(self, parent, f_audio, id_fenetre=-1, type_courbe='time'):
        global EVENT_FFT, EVENT_SPECTRO, PAGE_PLOT_FFT, PAGE_PLOT_SPECTRO
        wx.Panel.__init__(self, parent, id=id_fenetre)
        self.file_attente = queue.Queue()
        self.id_slider_beg = None
        self.id_slider_end = None
        self.id_bouton_copie =  None
        self.id_bouton_normaliser =  None
        self.id_bouton_compute =  None
        self.palette = None
        self.interface = None
        match type_courbe:
            case 'time':
                self.id_slider_beg = SLIDER_T_BEG
                self.id_slider_end = SLIDER_T_END
            case 'dft_modulus':
                self.id_slider_beg = SLIDER_FFT_BEG
                self.id_slider_end = SLIDER_FFT_END
                self.new_event_fft, self.id_evt_fft = wx.lib.newevent.NewEvent()
                self.Bind(self.id_evt_fft, self.update_axe_fft)
                PAGE_PLOT_FFT = self
                EVENT_FFT = self.new_event_fft
                self.id_bouton_copie =  BOUTON_COPY_FFT
                self.id_bouton_normaliser =  BOUTON_NORMALISER
            case 'dft_phase':
                self.id_slider_beg = SLIDER_FFT_BEG
                self.id_slider_end = SLIDER_FFT_END
                self.id_bouton_copie =  BOUTON_COPY_FFT
            case 'spectrogram':
                self.id_slider_beg = SLIDER_SPECTRO_BEG
                self.id_slider_end = SLIDER_SPECTRO_END
                self.new_event_spectro, self.id_evt_spectro = wx.lib.newevent.NewEvent()
                self.Bind(self.id_evt_spectro, self.update_axe_spectrogram)
                PAGE_PLOT_SPECTRO = self
                EVENT_SPECTRO = self.new_event_spectro
                self.id_bouton_copie =  BOUTON_COPY_SPECTRO
                self.palette = matplotlib.colormaps['magma']
            case 'Frequency response':
                self.id_bouton_compute =  BOUTON_COMPUTE_HZ
                
        self.flux_audio = f_audio
        self.flux_audio_ref = None
        self.type_courbe = type_courbe
        self.courbe_active = False
        self.parent = parent
        self.figure, self.graphique = plt.subplots()
        self.lines = None
        self.lines_ref =  None
        self.circle = None
        self.image = None
        self.bp_line = None
        self.bp_text = None
        self.bp_arrw = None
        self.peak_mark = None
        self.sig_audio = None
        self.mod_fft = None
        self.mod_fft_ref = None
        self.max_module = 1
        self.best_debug = False
        self.slider_t_beg = None
        self.slider_t_end = None
        self.val_x = None
        self.val_x_ref = None
        self.t_beg = 0
        self.t_end = self.flux_audio.nb_ech_fenetre
        self.pas = 1
        self.font = wx.Font(10,
                           wx.FONTFAMILY_DEFAULT,
                           wx.FONTSTYLE_NORMAL,
                           wx.FONTWEIGHT_BOLD)

        self.nb_data = 0 # nombre de données reçues
        self.graphique.yaxis.grid(True)
        self.figure.tight_layout(pad=0)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()
        self.auto_adjust = True
        self.samp_in_progress = False
        if type_courbe in ['time', 'dft_modulus']:
            self.max_module = self.flux_audio.nb_ech_fenetre /\
                              self.flux_audio.Fe
        presentation_fenetre = wx.BoxSizer(wx.VERTICAL)

        if self.id_slider_end is not None:
            style_texte = wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
            self.slider_t_beg = wx.Slider(self,
                        id=self.id_slider_beg,
                        value=self.t_beg,
                        minValue=0,
                        maxValue=self.t_end,
                        style=style_texte,
                        name="t begin")
            self.slider_t_beg.Bind(wx.EVT_SCROLL_CHANGED,
                                    self.change_slider,
                                    self.slider_t_beg,
                                    self.id_slider_beg)
            st_texte = wx.StaticText(self, label="begining index")
            presentation_fenetre.Add(st_texte, 0, wx.CENTER)
            presentation_fenetre.Add(self.slider_t_beg, 0, wx.EXPAND)
        if self.id_slider_end is not None:
            self.slider_t_end = wx.Slider(self,
                        id=self.id_slider_end,
                        value=self.t_end,
                        minValue=self.t_beg+1,
                        maxValue=self.flux_audio.taille_buffer_signal,
                        style=style_texte,
                        name="t end")
            self.slider_t_end.Bind(wx.EVT_SCROLL_CHANGED,
                            self.change_slider,
                            self.slider_t_end,
                            self.id_slider_end)
            st_texte = wx.StaticText(self, label="end index")
            presentation_fenetre.Add(st_texte, 0, wx.CENTER)
            presentation_fenetre.Add(self.slider_t_end, 0, wx.EXPAND)
        presentation_status = wx.BoxSizer(wx.HORIZONTAL)
        presentation_fenetre.Add(self.canvas, 1, wx.EXPAND)
        presentation_status.Add(self.toolbar, 0)
        if self.id_bouton_copie is not None:
            bouton = wx.Button(self, id=self.id_bouton_copie, label='Sync. Index')
            bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
            bouton.Bind(wx.EVT_BUTTON, self.synchronize_index, bouton)
            presentation_status.Add(bouton,0, wx.CENTER)
        if self.id_bouton_normaliser is not None:
            bouton = wx.Button(self, id=self.id_bouton_normaliser, label='Normalize')
            bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
            bouton.Bind(wx.EVT_BUTTON, self.normaliser, bouton)
            presentation_status.Add(bouton,0, wx.CENTER)
        if self.id_bouton_compute is not None:
            bouton = wx.Button(self, id=self.id_bouton_compute, label='Compute')
            bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
            bouton.Bind(wx.EVT_BUTTON, self.compute_hz, bouton)
            presentation_status.Add(bouton,0, wx.CENTER)



        self.info_curseur = wx.StaticText(self, label=100 * " ")
        self.info_curseur.SetFont(self.font)
        presentation_status.Add(self.info_curseur,0, wx.CENTER)
        presentation_fenetre.Add(presentation_status)
        # self.canvas.mpl_connect('motion_notify_event', self.UpdateCurseur)
        self.canvas.mpl_connect('button_press_event', self.UpdateCurseur)
        self.canvas.mpl_connect('key_press_event', self.on_key)
        self.SetSizer(presentation_fenetre)
        self.tps = 0
        self.thread_fft =  None
        self.init_axe()

    def synchronize_index(self, _evt):
        tps_fin = self.flux_audio.courbe.get_t_end('time')
        if tps_fin is not None:
            self.t_end = tps_fin
            self.slider_t_end.SetValue(self.t_end)
        tps_beg = self.flux_audio.courbe.get_t_beg('time')
        if tps_beg is not None:
            self.t_beg = tps_beg
            self.slider_t_beg.SetValue(self.t_beg)
        self.maj_limite_slider()
        self.init_axe()

    def set_interface(self, interface=None):
        if interface is not None:
            self._interface = interface
        return self._interface

    def normaliser(self, _evt):
        self.init_axe()

    def compute_hz(self, _evt):
        if not self.samp_in_progress and self.flux_audio_ref is not None:
            self.flux_audio_ref.compute_frequency_response(self.flux_audio.plotdata[:, 0])
            self.init_axe()

    def maj_limite_slider(self):
        if self.slider_t_end is not None:
            self.slider_t_end.SetMax(self.flux_audio.taille_buffer_signal)
            self.slider_t_end.SetMin(min(self.flux_audio.taille_buffer_signal-1, self.slider_t_beg.GetValue()))
            if self.t_end > self.flux_audio.taille_buffer_signal:
                self.t_end = self.flux_audio.taille_buffer_signal
        if self.slider_t_beg is not None:
            self.slider_t_beg.SetMax(self.flux_audio.taille_buffer_signal)
            self.slider_t_beg.SetValue(self.t_beg)
        if self.slider_t_end is not None:
            self.slider_t_end.SetValue(self.t_end)

    def set_t_beg(self, val):
        if self.slider_t_beg is not None:
            self.slider_t_beg.SetValue(val)
            self.t_beg = val

    def set_t_end(self, val):
        if self.slider_t_end is not None:
            self.slider_t_end.SetValue(val)
            self.t_end = val

    def set_t_max(self, val):
        if self.slider_t_end is not None:
            self.slider_t_end.SetMax(val)
        if self.slider_t_beg is not None:
            self.slider_t_beg.SetMax(self.t_end - 1)

    def change_slider(self, event):
        """
        réglage des glissiéres de temps
        """
        obj = event.GetEventObject()
        val = obj.GetValue()
        id_fenetre = event.GetId()
        if id_fenetre == self.id_slider_beg:
            self.t_beg = val
            self.slider_t_end.SetMin(val+1)
        if id_fenetre == self.id_slider_end:
            self.t_end = val
            self.slider_t_beg.SetMax(val)
        self.init_axe()
        r_upd = self.GetClientRect()
        self.Refresh(rect=r_upd)
        # self.flux_audio.courbe.draw_page(None)

    def computeBP(self, idx):
        bp_level = 10**(self.flux_audio.set_bp_level()/10)
        bp_inf = np.where(self.mod_fft[0:idx+1] < self.mod_fft[idx] * bp_level)
        if bp_inf[0].shape[0] > 0:
            idx_inf = bp_inf[0][-1]
        else:
            idx_inf =  0
        bp_sup = np.where(self.mod_fft[idx+1:self.flux_audio.tfd_size//2] < self.mod_fft[idx] * bp_level)
        if bp_sup[0].shape[0] > 0:
            idx_sup = bp_sup[0][0]+idx+1
        else:
            idx_sup =  self.flux_audio.tfd_size//2
            bp_level = 10**(self.flux_audio.set_bp_level()/10)
            bp_inf = np.where(self.mod_fft[0:idx+1] < self.mod_fft[idx] * bp_level)
            if bp_inf[0].shape[0] > 0:
                idx_inf = bp_inf[0][-1]
            else:
                idx_inf =  0
            bp_sup = np.where(self.mod_fft[idx+1:self.flux_audio.tfd_size//2] < self.mod_fft[idx] * bp_level)
            if bp_sup[0].shape[0] > 0:
                idx_sup = bp_sup[0][0]+idx+1
            else:
                idx_sup =  self.flux_audio.tfd_size//2
        mean_bp = np.mean(self.mod_fft[idx_inf: idx_sup])
        std_bp = np.std(self.mod_fft[idx_inf: idx_sup])
        return bp_level, idx_inf, idx_sup, mean_bp, std_bp
    
    def localise_freq(self, x, y):
        idx_freq = self.flux_audio.Fe / self.flux_audio.tfd_size
        idx_min, idx_max = self.graphique.get_xlim()
        y_min, y_max = self.graphique.get_ylim()
        offset = self.flux_audio.set_k_min()
        idx_min = int(np.round(idx_min / idx_freq)) - offset
        idx_max = int(np.round(idx_max / idx_freq)) - offset
        idx = np.argmin(np.abs(self.val_x-x))
        n_min = max(idx - 1000, idx_min)
        n_max = min(idx + 1000, idx_max)
        idx = np.argmin(np.abs(y - self.mod_fft[n_min + offset : n_max + offset]) / (y_max - y_min) +np.abs(x - self.val_x[n_min : n_max])/(idx_max-idx_min)) + n_min
        return idx + offset

    def draw_circle(self, freq, amp):
        bbox = self.graphique.get_window_extent().transformed(self.figure.dpi_scale_trans.inverted())
        width, height = bbox.width * self.figure.dpi, bbox.height * self.figure.dpi
        ratio_x = 16 / width
        ratio_y = 16 / height
        idx_min, idx_max = self.graphique.get_xlim()
        y_min, y_max = self.graphique.get_ylim()
        radius_x = (idx_max - idx_min) * ratio_x
        radius_y = (y_max - y_min) * ratio_y
        if self.circle is not None:
            self.circle.remove()
        self.circle = matplotlib.patches.Ellipse((freq, amp), radius_x, radius_y)
        self.graphique.add_artist(self.circle)
 
    def clear_circle(self):
        if self.circle is not None:
            self.circle.remove()
        self.circle = None

    def clear_peak(self):
        if self.peak_mark is not None:
            for line in self.peak_mark:
                line.remove()
            self.peak_mark = None
 
    def clear_bp(self):
        if self.bp_line is not None:
            self.bp_line.remove()
            self.bp_text.remove()
            self.bp_arrw.remove()
            self.bp_line = None
 

    def on_key(self, event):
        if event.key == 'delete':
            self.clear_bp()
            self.clear_peak()
            self.clear_circle()
            self.canvas.draw()


    def UpdateCurseur(self, event):
        if event.inaxes:
            try:
                idx_freq = self.flux_audio.Fe / self.flux_audio.tfd_size
            except ZeroDivisionError:
                wx.MessageBox("Division by zero. Try to synchronize index", "Error", wx.ICON_ERROR)
                return
            x, y = event.xdata, event.ydata
            if event.key == 'shift':
                match self.type_courbe:
                    case 'time':
                        if self.flux_audio.plotdata is not None:
                            idx = int(np.round(x))
                            a = self.flux_audio.plotdata[-self.flux_audio.nb_ech_fenetre+idx,:]
                            texte = [format(v,".3e") for v in a ]
                            self.info_curseur.SetLabel("Ech= " + str(idx) + " y=" + '/'.join(texte))
                            wx.LogMessage("Ech= " + str(idx) + " y=" + '/'.join(texte))
                            wx.LogMessage(40*'*')
                    case 'dft_modulus':
                         if self.flux_audio.plotdata is not None and self.mod_fft is not None:
                            idx = self.localise_freq(x, y)
                            a = self.mod_fft[idx]
                            texte = "f= " + self.flux_audio.get_format_precision(idx * idx_freq) + "(Hz)  module=" + format(a,".6e")
                            self.info_curseur.SetLabel(10 * " " + texte)
            if event.key == 'alt' and self.type_courbe == 'time':
                if int(np.round(x)) >self.t_beg:
                    self.t_end = int(np.round(x))
                    self.maj_limite_slider()
                    self.init_axe()
                    r_upd = self.GetClientRect()
                    self.Refresh(rect=r_upd)
            if event.key == 'control' and self.type_courbe == 'time':
                if int(np.round(x)) < self.t_end:
                    self.t_beg = int(np.round(x))
                    self.init_axe()
                    self.maj_limite_slider()
                    self.canvas.draw()
            if event.key == 'control' and self.type_courbe == 'dft_modulus':
                if self.flux_audio.plotdata is not None and self.mod_fft is not None:
                    idx = self.localise_freq(x, y)
                    wx.LogMessage('Selected frequency  ' + format(idx * idx_freq,'.5e') + "Hz")
                    bp_level = 10**(self.flux_audio.set_bp_level()/10)
                    pos_peak, _ = signal.find_peaks(self.mod_fft,
                                                    height= self.mod_fft[idx] * bp_level,
                                                    distance=self.flux_audio.set_peak_distance())
                    nb_peak = 0
                    if len(pos_peak) != 0:
                        texte = "Frequency(Hz)\tAmplitude(u.a.)\n"
                        wx.LogMessage("Frequency(Hz)\tAmplitude(u.a.)" )
                        for p in pos_peak:                   
                            if p > 0 and p < self.flux_audio.tfd_size // 2:
                                tmp_texte = str(self.flux_audio.get_format_precision(p * idx_freq)) + "\t" +\
                                        format(self.mod_fft[p], '.4e') + "\n"
                                wx.LogMessage(tmp_texte)
                                texte = texte + tmp_texte
                                nb_peak = nb_peak + 1
                                if nb_peak>=100:
                                    wx.LogMessage("Number of peaks is greater than 100")
                                    wx.LogMessage("Stop iterating")
                                    break
                        self.set_interface().sheet.message(texte)
                    if nb_peak <= 100:
                        pos = np.logical_and(pos_peak > 0, pos_peak < self.flux_audio.tfd_size // 2)
                        self.clear_peak()
                        self.peak_mark = self.graphique.plot(pos_peak[pos] * idx_freq, self.mod_fft[pos_peak[pos]], "x")
                        self.canvas.draw()
                    wx.LogMessage(40*'*')
            if event.key == 'shift+ctrl+shift' and self.type_courbe == 'dft_modulus':
                idx = self.localise_freq(x, y)
                n = 1
                texte = "Frequency(Hz)\tAmplitude(u.a.)\tT.H.D.(F)\n"
                wx.LogMessage(texte)
                pos_peak=[]
                amp_peak=[]
                thd = 0
                v1 = 0
                while n * idx < self.flux_audio.tfd_size//2:
                    pos = np.argmax(self.mod_fft[n * idx - self.flux_audio.set_peak_distance() + 1:n * idx+self.flux_audio.set_peak_distance()]) \
                          + n*idx - self.flux_audio.set_peak_distance() + 1
                    if n == 1:
                        v1 = self.mod_fft[pos]
                        if v1 == 0:
                            wx.MessageBox("fondamental amplitude is zero. Leaving", "Warning", wx.ICON_WARNING)
                            return
                    else:
                        thd = thd + self.mod_fft[pos]**2
                    amp_peak.append(self.mod_fft[pos])
                    pos_peak.append(pos*idx_freq)
                    tmp_texte = str(self.flux_audio.get_format_precision(pos * idx_freq)) + "\t" +\
                            format(self.mod_fft[pos], '.4e')+ "\t" +format(np.sqrt(thd)/v1, '.4e')  + "\n"
                    wx.LogMessage(tmp_texte)
                    texte = texte + tmp_texte
                    n = n + 1
                self.set_interface().sheet.message(texte)
                self.clear_peak()
                self.peak_mark = self.graphique.plot(pos_peak, amp_peak, "o")
                self.canvas.draw()

            if event.key == 'alt' and self.type_courbe == 'dft_modulus':
                idx = self.localise_freq(x, y)
                bp_level, idx_inf, idx_sup, mean_bp, std_bp = self.computeBP(idx)
                # http://www.dspguide.com
                texte = "Selected frequency(hz)\tModule( arb. unit)\tWidth at height( arb. unit)\tB(Hz)\tLow freq(Hz)\t High freq(Hz)\tMean( arb. unit)\tstd( arb. unit)\tCoefficient of variation(SNR=CV)"
                wx.LogMessage(texte)
                texte = texte + "\n" + str(self.flux_audio.get_format_precision(idx  * idx_freq))
                texte = texte + "\t" + format(self.mod_fft[idx], '.4e')
                texte = texte + "\t" + format(self.mod_fft[idx] * bp_level, '.4e')
                texte = texte + "\t" + self.flux_audio.get_format_precision((idx_sup - idx_inf) * idx_freq)
                texte = texte + "\t" + str(idx_inf * idx_freq) + '\t' +  str(idx_sup * idx_freq)
                texte = texte + "\t" + format(mean_bp, '.4e') + '\t' + format(std_bp, '.4e')
                texte = texte + "\t" + format(std_bp/mean_bp, '.4e')+ "\n" 
                if self.set_interface() is not None:
                    self.set_interface().sheet.message(texte)
                wx.LogMessage(texte)
                wx.LogMessage('Uncertainty  ' + format(2 * self.flux_audio.Fe/self.flux_audio.tfd_size, '.4e') + "Hz")
                wx.LogMessage(40*'*')
                self.clear_bp()
                self.bp_arrw = self.graphique.annotate(
                                        '',
                                        xy=(idx_inf * idx_freq, self.mod_fft[idx]* bp_level),
                                        xytext=(idx_sup * idx_freq, self.mod_fft[idx]* bp_level),
                                        arrowprops=dict(arrowstyle='<->'))
                self.bp_line = self.graphique.hlines(self.mod_fft[idx]* bp_level, idx_inf * idx_freq, idx_sup * idx_freq,
                                                     colors='k')
                texte = str(int(idx_inf * idx_freq)) + 'Hz <-> ' +  str(int(idx_sup * idx_freq)) + 'Hz'
                self.bp_text = self.graphique.text(idx_inf * idx_freq,self.mod_fft[idx]* bp_level,  texte)

                self.canvas.draw()

    def init_axe_time(self):
        plotdata = self.flux_audio.plotdata
        nb_ech_fenetre = self.flux_audio.nb_ech_fenetre
        self.val_x = np.arange(self.t_beg,self.t_end)
        self.lines = self.graphique.plot(self.val_x,plotdata[self.t_beg:self.t_end, :])
        self.graphique.axis((self.t_beg, self.t_end , -1, 1))
        self.graphique.legend(['channel -> u.a = f(ech)' + str(c)
                                for c in range(self.flux_audio.nb_canaux)],
                                loc='lower left',
                                ncol=self.flux_audio.nb_canaux)
        if self.flux_audio_ref is not None:
            d = self.flux_audio_ref.offset_synchro
            scale = max(1, (self.t_end - self.t_beg) // 2000)
            if d>0:
                self.lines_ref = self.graphique.plot(self.flux_audio_ref.plotdata[::scale])
            else:
                n = self.flux_audio_ref.plotdata.shape[0]
                self.lines_ref = self.graphique.plot(np.arange(-d, -d+n, scale), self.flux_audio_ref.plotdata[::scale])


    def init_axe_fft(self):
        self.flux_audio.set_tfd_size(self.t_end - self.t_beg)
        tfd_size = self.flux_audio.set_tfd_size()
        ratio = self.flux_audio.Fe / tfd_size
        self.val_x = np.arange(self.flux_audio.set_k_min(), self.flux_audio.set_k_max(), self.pas)
        self.val_x = self.val_x * ratio
        spec_selec = self.mod_fft[self.flux_audio.set_k_min():
                                    self.flux_audio.set_k_max():self.pas]
        self.max_module = spec_selec.max()
        if self.max_module == 0:
            self.max_module = 1
        self.lines = self.graphique.plot(self.val_x, spec_selec)
        self.graphique.axis((self.flux_audio.set_k_min() * ratio,
                             self.flux_audio.set_k_max() * ratio,
                             0,
                             1.1 * self.max_module))
        if not self.samp_in_progress and self.flux_audio_ref is not None:
            if self.lines_ref is not None:
                for line in self.lines_ref:
                    line.remove()
                self.lines_ref = None
            k_norm = self.max_module / self.flux_audio_ref.spec_selec.max()
            self.lines_ref = self.graphique.plot(self.flux_audio_ref.frequency,
                                                 self.flux_audio_ref.spec_selec * k_norm,
                                                 color='red')
            self.graphique.legend(['channel 0 -> u.a =f(Hz)','Spectrum reference'],
                                  loc='upper right')
        else:
            self.graphique.legend(['channel 0 -> u.a =f(Hz)'],
                                  loc='upper right')

    def init_axe_phase(self):
        self.flux_audio.set_tfd_size(self.t_end - self.t_beg)
        tfd_size = self.flux_audio.set_tfd_size()
        ratio = self.flux_audio.Fe / tfd_size
        self.val_x = np.arange(self.flux_audio.set_k_min(), self.flux_audio.set_k_max(), self.pas)
        self.val_x = self.val_x * ratio
        phase_selec = self.phase_fft[self.flux_audio.set_k_min():
                                    self.flux_audio.set_k_max():self.pas]
        if self.val_x.shape[0] != phase_selec.shape[0]:
            print("oops")
        self.lines = self.graphique.plot(self.val_x, phase_selec)
        self.graphique.axis((self.flux_audio.set_k_min() * ratio,
                             self.flux_audio.set_k_max() * ratio,
                             -np.pi,
                             np.pi))

    def init_axe_spectro(self):
        plotdata = self.flux_audio.plotdata[self.t_beg:self.t_end, 0]
        cols = np.arange(0, self.sxx_spectro.shape[1], max(1, self.sxx_spectro.shape[1]//4))
        temps = self.tps_spectro[0:self.tps_spectro.shape[0]:max(1, self.tps_spectro.shape[0]//4)]
        labels = [f"{x:.2e}s" for x in temps]
        self.graphique.set_xticks(cols, minor=False)
        self.graphique.set_xticklabels(labels, fontdict=None, minor=False)
        self.freq_ind_min = np.argmin(abs(self.f_spectro -
                                            self.flux_audio.f_min_spectro))
        self.freq_ind_max = np.argmin(abs(self.f_spectro -
                                            self.flux_audio.f_max_spectro))

        freq = self.f_spectro[self.freq_ind_min:self.freq_ind_max:
                    max(1, (self.freq_ind_max - self.freq_ind_min) // 4)]
        rows = np.arange(self.freq_ind_min,
                            self.freq_ind_max,
                            max(1,
                                (self.freq_ind_max - self.freq_ind_min) // 4))
        labels = [f"{x:.0f}Hz" for x in freq]
        self.graphique.set_yticks(rows, minor=False)
        self.graphique.set_yticklabels(labels, fontdict=None, minor=False,  rotation='vertical', verticalalignment='center')
        self.sxx_spectro[0, 0] = 1 / self.flux_audio.Fe
        self.image = self.graphique.imshow(self.sxx_spectro[self.freq_ind_min:
                                                            self.freq_ind_max,
                                                           :],
                                           origin='lower',
                                           aspect='auto',
                                           interpolation=None,
                                           filternorm=False,
                                           resample=False,
                                           cmap=self.palette)

    def init_axe(self):
        """
        Initialisation des axes pour tous les onglets
        """
        if self.flux_audio.plotdata is None:
            return
        if self.lines is not None:
            for ligne in self.lines:
                ligne.remove()
        if self.image:
            self.image.remove()
        if self.lines_ref:
            for ligne in self.lines_ref:
                ligne.remove()

        self.figure.gca().set_prop_cycle(None)
        self.lines = None
        self.image = None
        self.lines_ref = None
        plotdata = self.flux_audio.plotdata
        
        if self.best_debug:
            wx.LogDebug(str(self.flux_audio.nb_ech_fenetre))
            wx.LogDebug(str(self.flux_audio.set_tfd_size()))
            wx.LogDebug(str(self.flux_audio.set_k_min()))
            wx.LogDebug(str(self.flux_audio.set_k_max()))
        if self.type_courbe == 'Frequency response':
            if not self.samp_in_progress and self.flux_audio_ref is not None:
                N = self.flux_audio_ref.frequency.shape[0]
                self.graphique.plot(self.flux_audio_ref.frequency, np.abs(self.flux_audio_ref.freq_response[0:N]).real)
                self.canvas.draw()
        elif self.type_courbe == 'time':
            self.init_axe_time()
        elif self.type_courbe == 'dft_phase':
            self.flux_audio.set_tfd_size(self.t_end - self.t_beg)
            tfd_size = self.flux_audio.set_tfd_size()
            self.fft = np.fft.fft(plotdata[self.t_beg:self.t_end, 0])
            self.phase_fft = np.angle(self.fft)
            # self.phase_fft = fast_atan2(self.fft.imag, self.fft.real)
            self.init_axe_phase()
        elif self.type_courbe == 'dft_modulus':
            self.flux_audio.set_tfd_size(self.t_end - self.t_beg)
            tfd_size = self.flux_audio.set_tfd_size()
            if self.flux_audio.type_window[0] != 'boxcar':
                w = signal.get_window(tuple([self.flux_audio.type_window]),
                                      self.t_end - self.t_beg)
                self.fft = np.fft.fft(plotdata[self.t_beg:self.t_end, 0] * w)
            else:
                self.fft = np.fft.fft(plotdata[self.t_beg:self.t_end, 0])
            self.mod_fft = np.abs(self.fft).real / self.flux_audio.Fe
            self.max_module = self.mod_fft.max()
            self.init_axe_fft()
        elif self.type_courbe == 'spectrogram':
            spectro_size = self.t_end - self.t_beg # self.flux_audio.spectro_size
            self.f_spectro, self.tps_spectro, self.sxx_spectro = signal.spectrogram(
                plotdata[self.t_beg:self.t_end, 0],
                self.flux_audio.Fe,
                # window=(self.flux_audio.type_window),
                nperseg=self.flux_audio.win_size_spectro,
                noverlap=self.flux_audio.overlap_spectro)
            self.init_axe_spectro()

        if not self.courbe_active or self.type_courbe == 'time':
            self.canvas.draw()
            return None
        if self.nb_data > self.flux_audio.nb_ech_fenetre:
            self.nb_data = 0
            self.draw_page()

    def draw_page(self):
        """Tracer de la fenêtre en fonction
        du signal audio lors d'un événement
        les lignes et l'échelle du graphique ne sont pas modifiés
        """
        plot_data = self.flux_audio.plotdata
        if self.type_courbe == 'time':
            for column, line in enumerate(self.lines):
                line.set_ydata(plot_data[self.t_beg:self.t_end,column])
            return self.lines
        if self.type_courbe == 'dft_phase':
            pass
        if self.type_courbe == 'dft_modulus':
            if self.auto_adjust:
                self.max_module = -1
            for column, line in enumerate(self.lines):
                if self.flux_audio.type_window != ('boxcar'):
                    self.thread_fft = CalculFFT(plot_data[self.t_beg:self.t_end,column], self.flux_audio.Fe, self.flux_audio.type_window)
                else:
                    self.thread_fft = CalculFFT(plot_data[self.t_beg:self.t_end,column], self.flux_audio.Fe)
                self.thread_fft.start()
            self.auto_adjust = True
            return self.lines
        if self.type_courbe == 'spectrogram':
            self.thread_spectrogram = CalculSpectrogram(
                    self.flux_audio.plotdata[self.t_beg:self.t_end:, 0],
                    self.flux_audio.Fe,
                    self.flux_audio.win_size_spectro,
                    self.flux_audio.overlap_spectro,
                    self.flux_audio.type_window
                    )
            self.thread_spectrogram.start()
            return self.image

    def update_axe_fft(self, _evt):
        try:
            self.mod_fft = self.file_attente.get_nowait()
            max_fft = np.max(self.mod_fft[1:])
            if max_fft > self.max_module:
                self.max_module = max_fft
            spec_selec = self.mod_fft[self.flux_audio.set_k_min():
                                        self.flux_audio.set_k_max():self.pas]
            """
            val_x = np.arange(self.flux_audio.set_k_min(),
                                self.flux_audio.set_k_max(), self.pas) *\
                self.flux_audio.Fe / self.flux_audio.tfd_size
            """
            # self.lines[0].set_xdata(val_x)
            self.lines[0].set_ydata(spec_selec)
            return self.lines
        except queue.Empty:
            wx.LogError("Should not happen")
        return None

    def update_axe_spectrogram(self, _evt):
        try:
            self.spectro_audio = self.file_attente.get_nowait()
            psd = self.spectro_audio[self.freq_ind_min:self.freq_ind_max, :]
            self.image.set_data(psd)
            return self.image
        except queue.Empty:
            wx.LogError("Should not happen")
        return None

class Oscilloscope(wx.Panel):
    def __init__(self, parent, flux_a, id_fen=-1, evt_type=None):
        wx.Panel.__init__(self, parent, id=id_fen)
        self.flux_audio = flux_a
        NOTE_BOOK = self
        self.note_book = aui.AuiNotebook(self)
        sizer = wx.BoxSizer()
        sizer.Add(self.note_book, 1, wx.EXPAND)
        self.page = dict()
        self.evt_process = True
        self.SetSizer(sizer)
        self.parent = parent
        self.clock = time.perf_counter()
        self.Bind(evt_type[0], self.draw_pages)
        self.Bind(evt_type[1], self.new_gen_sig)
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CHANGED, self.init_axe)
        self.clock = 0
        self.interface = None

    def init_axe(self, _):
        idx_selec = self.note_book.GetSelection()
        for name in self.page:
            if self.page[name] == self.note_book.GetPage(idx_selec):
                self.page[name].init_axe()


    def set_interface(self, interface=None):
        self.interface = interface
        for nom in self.page:
            self.page[nom].set_interface(interface)

    def add(self, name="plot", type_courbe='time'):
        """ Ajout d'un onglet au panel
        """
        if type_courbe in self.page.keys():
            wx.MessageBox("Page already exist",
                          "Error",
                          wx.ICON_ERROR)
            return None
        page = Plot(self.note_book, self.flux_audio, type_courbe=type_courbe)
        self.page[type_courbe] = page
        self.note_book.AddPage(page, name)
        self.note_book.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.close_page)

        return page

    def draw_circle(self, freq, amp):
        self.page['dft_modulus'].draw_circle(freq, amp)
        self.page['dft_modulus'].canvas.draw()


    def clear_circle(self):
        self.page['dft_modulus'].clear_circle()
        self.page['dft_modulus'].canvas.draw()

    def draw_pages(self, _evt):
        """ tracé de la courbe associé à l'onglet
        """

        # if time.perf_counter() - self.clock < 3*self.flux_audio.tps_refresh:
        #    self.evt_process = True
        #    return
        # self.clock = time.perf_counter()
        nb_data = self.flux_audio.new_sample()
        if nb_data > self.flux_audio.nb_ech_fenetre:
            self.page['time'].nb_data = 0
            for name in self.page:
                if self.page[name].courbe_active:
                    self.page[name].draw_page()
                    self.page[name].canvas.draw()
        self.evt_process = True

    def new_gen_sig(self, evt):
        """ 
        Nouveau signal généré
        """

        idx_selec = self.note_book.GetSelection()
        for name in self.page:
            if evt.attr1 != 0:
                if self.page[name].t_end >= evt.attr2:
                    self.page[name].t_end = self.flux_audio.taille_buffer_signal
                    if self.page[name].t_beg != 0:
                        self.page[name].t_beg = self.flux_audio.taille_buffer_signal - evt.attr2 + self.page[name].t_beg
                        if self.page[name].t_beg <0:
                            self.page[name].t_beg = 0
                        elif self.page[name].t_beg >= self.page[name].t_end:
                            self.page[name].t_beg = self.page[name].t_end - 1
            self.page[name].maj_limite_slider()
            if self.page[name] == self.note_book.GetPage(idx_selec):
                self.page[name].init_axe()
        self.evt_process = True
        if self.interface is not None:
            self.interface.maj_choix_freq()

    def maj_palette(self, page_name, pal_name):
        """ changement de palette 
        """
        if page_name in self.page.keys():
            self.page[page_name].palette = matplotlib.colormaps[pal_name]
            if page_name == 'spectrogram':
                self.page[page_name].init_axe()
            self.page[page_name].draw_page()
            self.page[page_name].canvas.draw()

    def maj_page(self, page_name):
        """ tracé de la courbe associé à l'onglet
        """

        if page_name in self.page.keys():
            if self.page[page_name].courbe_active:
                self.page[page_name].draw_page()
                self.page[page_name].canvas.draw()

    def get_t_beg(self, page_name):
        if page_name in self.page.keys():
            return self.page[page_name].t_beg
        return None

    def get_t_end(self, page_name):
        if page_name in self.page.keys():
            return self.page[page_name].t_end
        return None        

    def set_t_beg(self, val):
        for name in self.page:
            self.page[name].set_t_beg(val)
        return None

    def set_t_end(self, val):
        for name in self.page:
            self.page[name].set_t_end(val)
        return None        

    def set_t_max(self, val):
        for name in self.page:
            self.page[name].set_t_max(val)
        return None        

    def maj_limite_slider(self):
        for name in self.page:
            self.page[name].maj_limite_slider()

    def draw_all_axis(self):
        idx_selec = self.note_book.GetSelection()
        for name in self.page:
            if self.page[name] == self.note_book.GetPage(idx_selec):
                self.page[name].init_axe()

    def close_page(self, evt):
        wx.MessageBox("Cannot be closed", "Warning", wx.ICON_WARNING)
        evt.Veto()
