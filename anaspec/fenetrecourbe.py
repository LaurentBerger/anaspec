"""
A DEFINIR

"""

import time
import queue
import threading
import numpy as np
from scipy import signal

import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg\
   as NavigationToolbar

import wx
import wx.lib.newevent
import wx.lib.agw.aui as aui

# pylint: disable=maybe-no-member
EVENT_FFT = None
EVENT_SPECTRO = None
PAGE_PLOT_FFT = None
PAGE_PLOT_SPECTRO = None

class CalculFFT(threading.Thread):
    """ calcul de la fft en utilisant un thread
    et envoie d'un événement en fin de calcul
    """
    def __init__(self, x, fe):
        threading.Thread.__init__(self)
        self.x = x.copy()
        self.Fe = fe
    
    def run(self):
        self.z = np.fft.fft(self.x)
        self.z = np.abs(self.z).real / self.Fe
        evt = EVENT_FFT(attr1="CalculFFT", attr2=0)
        # Envoi de l'événement à la fenêtre chargée du tracé
        if PAGE_PLOT_FFT:
            wx.PostEvent(PAGE_PLOT_FFT, evt)

class CalculSpectrogram(threading.Thread):
    """ calcul du spectrogramme en utilisant un thread
    et envoie d'un événement en fin de calcul
    """
    def __init__(self, x, fe, win_size_spectro, overlap_spectro):
        threading.Thread.__init__(self)
        self.x = x.copy()
        self.Fe = fe
        self.win_size_spectro = win_size_spectro
        self.overlap_spectro = overlap_spectro
    
    def run(self):
        _, _, self.z = signal.spectrogram(
                self.x,
                self.Fe,
                nperseg=self.win_size_spectro,
                noverlap=self.overlap_spectro)
        evt = EVENT_SPECTRO(attr1="CalculSpectrogram", attr2=0)
        # Envoi de l'événement à la fenêtre chargée du tracé
        if PAGE_PLOT_SPECTRO:
            wx.PostEvent(PAGE_PLOT_SPECTRO, evt)


class Plot(wx.Panel):
    """
    Fenetrage wx contenant un graphique matplotlib
    """
    def __init__(self, parent, f_audio, id_fenetre=-1, type_courbe='time'):
        global EVENT_FFT, EVENT_SPECTRO, PAGE_PLOT_FFT, PAGE_PLOT_SPECTRO
        wx.Panel.__init__(self, parent, id=id_fenetre)
        if type_courbe == 'dft_modulus':
            self.new_event_fft, self.id_evt_fft = wx.lib.newevent.NewEvent()
            self.Bind(self.id_evt_fft, self.update_axe_fft)
            PAGE_PLOT_FFT = self
            EVENT_FFT = self.new_event_fft
        if type_courbe == 'spectrogram':
            self.new_event_spectro, self.id_evt_spectro = wx.lib.newevent.NewEvent()
            self.Bind(self.id_evt_spectro, self.update_axe_spectrogram)
            PAGE_PLOT_SPECTRO = self
            EVENT_SPECTRO = self.new_event_spectro
        self.flux_audio = f_audio
        self.type_courbe = type_courbe
        self.courbe_active = False
        self.parent = parent
        self.figure, self.graphique = plt.subplots()
        self.lines = None
        self.image = None
        self.sig_audio = None
        self.fft_audio = None
        self.init_axe()
        self.graphique.yaxis.grid(True)
        self.figure.tight_layout(pad=0)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()
        self.auto_adjust = True
        self.best_debug = False
        self.font = wx.Font(10,
                           wx.FONTFAMILY_DEFAULT,
                           wx.FONTSTYLE_NORMAL,
                           wx.FONTWEIGHT_BOLD)

        self.nb_data = 0 # nombre de données reçues
        if type_courbe in ['time', 'dft_modulus']:
            self.max_module = self.flux_audio.nb_ech_fenetre /\
                              self.flux_audio.Fe
        presentation_fenetre = wx.BoxSizer(wx.VERTICAL)
        presentation_status = wx.BoxSizer(wx.HORIZONTAL)
        presentation_fenetre.Add(self.canvas, 1, wx.EXPAND)
        presentation_status.Add(self.toolbar, 0)
        self.info_curseur = wx.StaticText(self, label="")
        self.info_curseur.SetFont(self.font)
        presentation_status.Add(self.info_curseur,wx.EXPAND)
        presentation_fenetre.Add(presentation_status)
        self.canvas.mpl_connect('motion_notify_event', self.UpdateCurseur)
        self.SetSizer(presentation_fenetre)
        self.tps = 0

    def UpdateCurseur(self, event):
        if event.inaxes:
            x, y = event.xdata, event.ydata
            match self.type_courbe:
                case 'time':
                    if self.flux_audio.plotdata is not None:
                        idx = int(np.round(x))
                        a = self.flux_audio.plotdata[-self.flux_audio.nb_ech_fenetre+idx,:]
                        texte = [format(v,".3e") for v in a ]
                        self.info_curseur.SetLabel("Ech= " + str(idx) + "(s)  y=" + '/'.join(texte))
                case 'dft_modulus':
                     if self.flux_audio.plotdata is not None and self.fft_audio is not None:
                        idx = int(np.round(self.flux_audio.tfd_size * x /self.flux_audio.Fe))
                        if 0 <= idx < self.flux_audio.tfd_size:
                            a = self.fft_audio[idx]
                            texte = "f= " + format(idx * self.flux_audio.Fe / self.flux_audio.tfd_size, ".2e") + "(Hz)  module=" + format(a,".3e")
                            self.info_curseur.SetLabel(texte)

    def init_axe_time(self):
        plotdata = self.flux_audio.plotdata
        nb_ech_fenetre = self.flux_audio.nb_ech_fenetre
        self.lines = self.graphique.plot(plotdata[-nb_ech_fenetre:, :])
        self.graphique.axis((0, nb_ech_fenetre , -1, 1))
        self.graphique.legend(['channel ' + str(c)
                                for c in range(self.flux_audio.nb_canaux)],
                                loc='lower left',
                                ncol=self.flux_audio.nb_canaux)

    def init_axe_fft(self):
        tfd_size = self.flux_audio.tfd_size
        val_x = np.arange(self.flux_audio.k_min, self.flux_audio.k_max) *\
                self.flux_audio.Fe / tfd_size
        spec_selec = self.fft_audio[self.flux_audio.k_min:
                                    self.flux_audio.k_max]
        self.max_module = tfd_size / self.flux_audio.Fe
        self.lines = self.graphique.plot(val_x, spec_selec)
        self.graphique.axis((self.flux_audio.k_min * self.flux_audio.Fe /
                                tfd_size,
                                self.flux_audio.k_max*self.flux_audio.Fe /
                                tfd_size,
                                0,
                                self.max_module))
        self.graphique.legend(['channel ' + str(c)
                                for c in range(self.flux_audio.nb_canaux)],
                                loc='upper right',
                                ncol=self.flux_audio.nb_canaux)

    def init_axe_spectro(self):
        plotdata = self.flux_audio.plotdata
        cols = np.arange(0, self.sxx_spectro.shape[1], max(1, self.sxx_spectro.shape[1]//4))
        temps = self.tps_spectro[0:self.tps_spectro.shape[0]:max(1, self.tps_spectro.shape[0]//4)]
        labels = [f"{x:.2e}" for x in temps]
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
        labels = [f"{x:.0f}" for x in freq]
        self.graphique.set_yticks(rows, minor=False)
        self.graphique.set_yticklabels(labels, fontdict=None, minor=False)
        self.sxx_spectro[0, 0] = 1 / self.flux_audio.Fe
        self.image = self.graphique.imshow(self.sxx_spectro[self.freq_ind_min:
                                                            self.freq_ind_max,
                                                           :],
                                           origin='lower',
                                           aspect='auto')

    def init_axe(self):
        if self.flux_audio.plotdata is None:
            return
        if self.lines is not None:
            for ligne in self.lines:
                ligne.remove()
        if self.image:
            self.image.remove()
        self.figure.gca().set_prop_cycle(None)
        self.lines = None
        self.image = None
        plotdata = self.flux_audio.plotdata
        
        if self.best_debug:
            print( self.flux_audio.nb_ech_fenetre)
            print( self.flux_audio.tfd_size)
            print( self.flux_audio.k_min)
            print( self.flux_audio.k_max)
        if self.type_courbe == 'time':
            self.init_axe_time()
        elif self.type_courbe == 'dft_modulus':
            tfd_size = self.flux_audio.tfd_size
            self.fft_audio = np.fft.fft(plotdata[-tfd_size:, 0])
            self.fft_audio = np.abs(self.fft_audio).real / self.flux_audio.Fe
            self.init_axe_fft()
        elif self.type_courbe == 'spectrogram':
            spectro_size = self.flux_audio.spectro_size
            self.f_spectro, self.tps_spectro, self.sxx_spectro = signal.spectrogram(
                plotdata[-spectro_size:, 0],
                self.flux_audio.Fe,
                window=(self.flux_audio.type_window),
                nperseg=self.flux_audio.win_size_spectro,
                noverlap=self.flux_audio.overlap_spectro)
            self.init_axe_spectro()

        if not self.courbe_active:
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
                line.set_ydata(plot_data[-self.flux_audio.nb_ech_fenetre:,column])
            return self.lines
        if self.type_courbe == 'dft_modulus':
            if self.auto_adjust:
                self.max_module = -1
            for column, line in enumerate(self.lines):
                self.thread_fft = CalculFFT(plot_data[-self.flux_audio.tfd_size:,column], self.flux_audio.Fe)
                self.thread_fft.start()
            self.auto_adjust = True
            return self.lines
        if self.type_courbe == 'spectrogram':
            self.thread_spectrogram = CalculSpectrogram(
                    self.flux_audio.plotdata[-self.flux_audio.spectro_size:, 0],
                    self.flux_audio.Fe,
                    self.flux_audio.win_size_spectro,
                    self.flux_audio.overlap_spectro
                    )
            self.thread_spectrogram.start()
            return self.image

    def update_axe_fft(self, _evt):
        self.fft_audio = self.thread_fft.z
        if self.auto_adjust:
            max_fft = np.max(self.fft_audio[1:])
            if max_fft > self.max_module:
                self.max_module = max_fft
        spec_selec = self.fft_audio[self.flux_audio.k_min:
                                    self.flux_audio.k_max]
        val_x = np.arange(self.flux_audio.k_min,
                            self.flux_audio.k_max) *\
            self.flux_audio.Fe / self.flux_audio.tfd_size
        self.lines[0].set_xdata(val_x)
        self.lines[0].set_ydata(spec_selec)
        return self.lines

    def update_axe_spectrogram(self, _evt):
        self.spectro_audio = self.thread_spectrogram.z
        psd = self.spectro_audio[self.freq_ind_min:self.freq_ind_max, :]
        self.image.set_data(psd)
        return self.image

class PlotNotebook(wx.Panel):
    def __init__(self, parent, flux_a, id_fen=-1, evt_type=None):
        wx.Panel.__init__(self, parent, id=id_fen)
        self.flux_audio = flux_a
        NOTE_BOOK = self
        self.note_book = aui.AuiNotebook(self)
        sizer = wx.BoxSizer()
        sizer.Add(self.note_book, 1, wx.EXPAND)
        self.page = []
        self.evt_process = True
        self.SetSizer(sizer)
        self.parent = parent
        self.clock = time.perf_counter()
        self.Bind(evt_type, self.draw_page)
        self.clock = 0

    def add(self, name="plot", type_courbe='time'):
        """ Ajout d'un onglet au panel
        """
        page = Plot(self.note_book, self.flux_audio, type_courbe=type_courbe)
        self.page.append(page)
        self.note_book.AddPage(page, name)
        self.note_book.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.close_page)

        return page

    def draw_page(self, _evt):
        """ tracé de la courbe associé à l'onglet
        """

        if time.perf_counter() - self.clock < 3*self.flux_audio.tps_refresh:
            self.evt_process = True
            return
        self.clock = time.perf_counter()
        nb_data = self.flux_audio.new_sample()
        if nb_data > self.flux_audio.nb_ech_fenetre:
            self.page[0].nb_data = 0
            for page in self.page:
                if page.courbe_active:
                    page.draw_page()
                    page.canvas.draw()
        self.evt_process = True

    def draw_all_axis(self):
        for page in self.page:
            page.init_axe()

    def close_page(self, evt):
        wx.MessageBox("Cannot be closed", "Warning", wx.ICON_WARNING)
        evt.Veto()
