import time
import queue
import numpy as np
from scipy import signal

import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar

import wx
import wx.lib.newevent
import wx.lib.agw.aui as aui


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
        self.etendue_axe()
        self.graphique.yaxis.grid(True)
        self.figure.tight_layout(pad=0)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()
        self.auto_adjust = True
        if type_courbe in ['time', 'dft_modulus']:
            self.max_module = self.flux_audio.nb_ech_fenetre / self.flux_audio.Fe
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        self.SetSizer(sizer)
        self.tps = 0

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
        if self.type_courbe == 'time':
            self.lines = self.graphique.plot(self.flux_audio.plotdata[-self.flux_audio.nb_ech_fenetre:, :])
            self.graphique.axis((0, len(self.flux_audio.plotdata[-self.flux_audio.nb_ech_fenetre:, :]) / 
                                 self.flux_audio.nb_canaux, -1, 1))
            self.graphique.legend(['channel {}'.format(c) for c in range(self.flux_audio.nb_canaux)],
                           loc='lower left', ncol=self.flux_audio.nb_canaux)
        elif self.type_courbe == 'dft_modulus':
            self.lines = self.graphique.plot(self.flux_audio.plotdata[-self.flux_audio.nb_ech_fenetre:, :])
            self.graphique.axis((self.flux_audio.k_min*self.flux_audio.Fe /
                                 self.flux_audio.nb_ech_fenetre,
                                 self.flux_audio.k_max*self.flux_audio.Fe /
                                 self.flux_audio.nb_ech_fenetre,
                          0,
                          self.max_module))
            self.graphique.legend(['channel {}'.format(c) 
                                   for c in range(self.flux_audio.nb_canaux)],
                                   loc='upper right', ncol=self.flux_audio.nb_canaux)
        elif self.type_courbe == 'spectrogram':
            freq, temps, sxx = signal.spectrogram(
                self.flux_audio.plotdata[-self.flux_audio.nb_ech_fenetre:, 0],
                self.flux_audio.Fe,
                window = (self.flux_audio.type_window),
                nperseg=self.flux_audio.win_size_spectro,
                noverlap=self.flux_audio.overlap_spectro)
            temps = temps[0:temps.shape[0]:max(1, temps.shape[0]//4)]
            cols = np.arange(0, sxx.shape[1], max(1, sxx.shape[1]//4))
            labels = ["{:.2e}".format(x) for x in temps]
            self.graphique.set_xticks(cols, minor=False)
            self.graphique.set_xticklabels(labels, fontdict=None, minor=False)
            self.freq_ind_min = np.argmin(abs(freq-self.flux_audio.f_min_spectro))
            self.freq_ind_max = np.argmin(abs(freq-self.flux_audio.f_max_spectro))

            freq = freq[self.freq_ind_min:self.freq_ind_max:
                  max(1, (self.freq_ind_max - self.freq_ind_min) // 4)]
            rows = np.arange(self.freq_ind_min,
                             self.freq_ind_max,
                             max(1, (self.freq_ind_max - self.freq_ind_min) // 4))
            labels = ["{:.0f}".format(x) for x in freq]
            self.graphique.set_yticks(rows, minor=False)
            self.graphique.set_yticklabels(labels, fontdict=None, minor=False)
            sxx[0, 0] = 1 / self.flux_audio.Fe
            self.image = self.graphique.imshow(sxx[self.freq_ind_min:self.freq_ind_max, :],
                                        origin='lower',
                                        aspect='auto')

    def draw_page(self):
        """Tracer de la fenêtre en fonction
        du signal audio
        """
        while True:
            try:
                # https://docs.python.org/3/library/queue.html#queue.Queue.get_nowait
                data = self.flux_audio.q.get_nowait()
            except queue.Empty:
                break
            shift = len(data)
            # print("data shape :", data.shape)
            # print("plotdata shape :", self.flux_audio.plotdata.shape)
            if shift<self.flux_audio.plotdata.shape[0]:
                self.flux_audio.plotdata = np.roll(self.flux_audio.plotdata, -shift, axis=0)
                self.flux_audio.plotdata[-shift:, :] = data
            else:
                return None
        if not self.courbe_active:
            return None
        if self.type_courbe == 'time':
            for column, line in enumerate(self.lines):
                line.set_ydata((column+1) *self.flux_audio.plotdata[-self.flux_audio.nb_ech_fenetre:, column])
            return self.lines
        elif self.type_courbe == 'dft_modulus':
            if self.auto_adjust:
                self.max_module = -1
            for column, line in enumerate(self.lines):
                fft_audio = np.fft.fft(self.flux_audio.plotdata[-self.flux_audio.nb_ech_fenetre:, column])
                fft_audio = np.abs(fft_audio).real / self.flux_audio.Fe
                if self.auto_adjust:
                    max_fft = np.max(fft_audio)
                    print(max_fft)
                    if max_fft > self.max_module:
                        self.max_module = max_fft
                spec_selec = fft_audio[self.flux_audio.k_min:self.flux_audio.k_max]
                #line.set_xdata(np.arange(self.flux_audio.k_min, self.flux_audio.k_max) *
                #               self.flux_audio.Fe / self.flux_audio.nb_ech_fenetre)
                #line.set_ydata(spec_selec)
            self.lines = self.graphique.plot(self.flux_audio.plotdata[-self.flux_audio.nb_ech_fenetre:, :])
            self.auto_adjust = True
            return self.lines
        elif self.type_courbe == 'spectrogram':
            _, _, spectro = signal.spectrogram(
                self.flux_audio.plotdata[-self.flux_audio.nb_ech_fenetre:, column],
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
                page.draw_page()
                page.canvas.draw()
                page.canvas.flush_events()
        self.evt_process = True

    def etendue_axe(self, _):
        for page in self.page:
            page.etendue_axe()

    def close_page(self, evt):
        wx.MessageBox("Cannot be closed", "Warning", wx.ICON_WARNING)
        evt.Veto()
