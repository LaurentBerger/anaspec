import time
import queue
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar

import wx
import wx.lib.newevent
import wx.lib.agw.aui as aui


class Plot(wx.Panel):
    """
    Fenetage wx contenant un graphique matplotlib
    """
    def __init__(self, parent, fa, id=-1, type_courbe='time'):
        wx.Panel.__init__(self, parent, id=id)
        self.fa = fa
        self.type_courbe = type_courbe
        self.parent = parent
        self.figure, self.ax = plt.subplots()
        self.lines = None
        self.etendue_axe()
        self.ax.yaxis.grid(True)
        self.figure.tight_layout(pad=0)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        self.SetSizer(sizer)

    def etendue_axe(self):
        if self.fa.plotdata is None:
            return
        if self.lines is not None:
            for l in self.lines:
                l.remove()
        self.figure.gca().set_prop_cycle(None)
        self.lines = self.ax.plot(self.fa.plotdata)
        self.ax.legend(['channel {}'.format(c) for c in range(self.fa.nb_canaux)],
                       loc='lower left', ncol=self.fa.nb_canaux)
        if self.type_courbe == 'time':
            self.ax.axis((0, len(self.fa.plotdata)/self.fa.nb_canaux, -1, 1))
        elif self.type_courbe == 'dft_modulus':
            freq = np.fft.fftfreq(self.fa.nb_ech_fenetre)*self.fa.Fe
            self.ax.axis((0, self.fa.nb_ech_fenetre//2, 0, len(self.fa.plotdata)))


    def draw_page(self):
        """Tracer de la fenêtre en fonction
        du signal audio
        """
        while True:
            try:
                data = self.fa.q.get_nowait()
            except queue.Empty:
                break
            shift = len(data)
            self.fa.plotdata = np.roll(self.fa.plotdata, -shift, axis=0)
            self.fa.plotdata[-shift:, :] = data
        if self.type_courbe == 'time':
            for column, line in enumerate(self.lines):
                line.set_ydata((column+1) *self.fa.plotdata[:, column])
            return self.lines
        elif self.type_courbe == 'dft_modulus':
            S =  np.abs(np.fft.fft(self.fa.plotdata[0:self.fa.nb_ech_fenetre, 0])).real
            self.ax.axis((0, self.fa.Fe/2, 0, 1))
            p = S[0:self.fa.nb_ech_fenetre//2+1]
            self.lines[0].set_ydata(p)

class PlotNotebook(wx.Panel):
    def __init__(self, parent, fa, id=-1, evt_type=None):
        wx.Panel.__init__(self, parent, id=id)
        self.fa = fa
        self.nb = aui.AuiNotebook(self)
        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        self.page = []
        self.SetSizer(sizer)
        self.parent = parent
        self.Bind(evt_type, self.draw_page)
        self.clock = 0

    def add(self, name="plot", type_courbe='time'):
        """ Ajout d'un onglet au panel
        """
        page = Plot(self.nb, self.fa, type_courbe=type_courbe)
        self.page.append(page)
        self.nb.AddPage(page, name)
        self.nb.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.close_page)
        return page

    def close_page(self, evt):
        wx.MessageBox("Cannot be closed", "Warning", wx.ICON_WARNING)
        evt.Veto()

    def draw_page(self, _evt):
        """ tracé de la courbe associé à l'onglet
        """
        if time.clock() - self.clock < self.fa.tps_refresh:
            return
        self.clock = time.clock()
        for page in self.page:
            if self.nb.GetCurrentPage() == page:
                page.draw_page()
                page.canvas.draw()

    def etendue_axe(self, etendue):
        for page in self.page:
            page.etendue_axe()
