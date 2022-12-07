"""
A DEFINIR

"""

import time
import queue
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


class Plot(wx.Panel):
    """
    Fenetrage wx contenant un graphique matplotlib
    """
    def __init__(self, parent, f_audio, id_fenetre=-1, type_courbe='time'):
        wx.Panel.__init__(self, parent, id=id_fenetre)
        self.flux_audio = f_audio
        self.type_courbe = type_courbe
        self.courbe_active = False
        self.parent = parent
        self.figure, self.graphique = plt.subplots()
        self.lines = None
        self.image = None
        self.sig_audio = None
        self.fft_audio = None
        self.etendue_axe()
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
                            texte = "f= " + str(idx * self.flux_audio.Fe / self.flux_audio.tfd_size) + "(Hz)  module=" + format(a,".3e")
                            self.info_curseur.SetLabel(texte)


    def etendue_axe(self):
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
            nb_ech_fenetre = self.flux_audio.nb_ech_fenetre
            self.lines = self.graphique.plot(plotdata[-nb_ech_fenetre:, :])
            self.graphique.axis((0, nb_ech_fenetre , -1, 1))
            self.graphique.legend(['channel ' + str(c)
                                   for c in range(self.flux_audio.nb_canaux)],
                                  loc='lower left',
                                  ncol=self.flux_audio.nb_canaux)
        elif self.type_courbe == 'dft_modulus':
            tfd_size = self.flux_audio.tfd_size
            val_x = np.arange(self.flux_audio.k_min, self.flux_audio.k_max) *\
                    self.flux_audio.Fe / tfd_size
            self.fft_audio = np.fft.fft(plotdata[-tfd_size:, 0])
            self.fft_audio = np.abs(self.fft_audio).real / self.flux_audio.Fe
            spec_selec = self.fft_audio[self.flux_audio.k_min:
                                        self.flux_audio.k_max]
            self.max_module = tfd_size / self.flux_audio.Fe / 10
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
        elif self.type_courbe == 'spectrogram':
            spectro_size = self.flux_audio.spectro_size
            freq, temps, sxx = signal.spectrogram(
                plotdata[-spectro_size:, 0],
                self.flux_audio.Fe,
                window=(self.flux_audio.type_window),
                nperseg=self.flux_audio.win_size_spectro,
                noverlap=self.flux_audio.overlap_spectro)
            temps = temps[0:temps.shape[0]:max(1, temps.shape[0]//4)]
            cols = np.arange(0, sxx.shape[1], max(1, sxx.shape[1]//4))
            labels = [f"{x:.2e}" for x in temps]
            self.graphique.set_xticks(cols, minor=False)
            self.graphique.set_xticklabels(labels, fontdict=None, minor=False)
            self.freq_ind_min = np.argmin(abs(freq -
                                              self.flux_audio.f_min_spectro))
            self.freq_ind_max = np.argmin(abs(freq -
                                              self.flux_audio.f_max_spectro))

            freq = freq[self.freq_ind_min:self.freq_ind_max:
                        max(1, (self.freq_ind_max - self.freq_ind_min) // 4)]
            rows = np.arange(self.freq_ind_min,
                             self.freq_ind_max,
                             max(1,
                                 (self.freq_ind_max - self.freq_ind_min) // 4))
            labels = [f"{x:.0f}" for x in freq]
            self.graphique.set_yticks(rows, minor=False)
            self.graphique.set_yticklabels(labels, fontdict=None, minor=False)
            sxx[0, 0] = 1 / self.flux_audio.Fe
            self.image = self.graphique.imshow(sxx[self.freq_ind_min:
                                                   self.freq_ind_max,
                                                   :],
                                               origin='lower',
                                               aspect='auto')

    def new_sample(self):
        """ Réception de nouvelle données
        du signal audio
        """
        while True:
            try:
                # https://docs.python.org/3/library/queue.html#queue.Queue.get_nowait
                data = self.flux_audio.file_attente.get_nowait()
            except queue.Empty:
                break

            shift = data.shape[0]
            self.nb_data = self.nb_data + shift
            # print("data shape :", data.shape)
            # print("plotdata shape :", self.flux_audio.plotdata.shape)
            if shift < self.flux_audio.plotdata.shape[0]:
                self.flux_audio.plotdata = np.roll(self.flux_audio.plotdata,
                                                   -shift,
                                                   axis=0)
                self.flux_audio.plotdata[-shift:, :] = data
            else:
                return None
        if not self.courbe_active:
            return None
        if self.nb_data > self.flux_audio.nb_ech_fenetre:
            self.nb_data = 0
            self.draw_page()

    def draw_page(self):
        """Tracer de la fenêtre en fonction
        du signal audio
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
                self.fft_audio = np.fft.fft(
                                plot_data[-self.flux_audio.tfd_size:,
                                          column])
                self.fft_audio = np.abs(self.fft_audio).real / self.flux_audio.Fe
                if self.auto_adjust:
                    max_fft = np.max(self.fft_audio)
                    if max_fft > self.max_module:
                        self.max_module = max_fft
                spec_selec = self.fft_audio[self.flux_audio.k_min:
                                            self.flux_audio.k_max]
                val_x = np.arange(self.flux_audio.k_min,
                                  self.flux_audio.k_max) *\
                    self.flux_audio.Fe / self.flux_audio.tfd_size
                line.set_xdata(val_x)
                line.set_ydata(spec_selec)
            self.auto_adjust = True
            return self.lines
        if self.type_courbe == 'spectrogram':
            _, _, spectro = signal.spectrogram(
                self.flux_audio.plotdata[-self.flux_audio.spectro_size:, 0],
                self.flux_audio.Fe,
                nperseg=self.flux_audio.win_size_spectro,
                noverlap=self.flux_audio.overlap_spectro)

            psd = spectro[self.freq_ind_min:self.freq_ind_max, :]
            self.image.set_data(psd)
            return self.image



class PlotNotebook(wx.Panel):
    def __init__(self, parent, flux_a, id_fen=-1, evt_type=None):
        wx.Panel.__init__(self, parent, id=id_fen)
        self.flux_audio = flux_a
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
        for page in self.page:
            if page.courbe_active:
                page.new_sample()
                page.canvas.draw()
        self.evt_process = True

    def etendue_axe(self, _):
        for page in self.page:
            page.etendue_axe()

    def close_page(self, evt):
        wx.MessageBox("Cannot be closed", "Warning", wx.ICON_WARNING)
        evt.Veto()
