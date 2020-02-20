import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar

import wx
import wx.lib.newevent
import wx.lib.agw.aui as aui


class Plot(wx.Panel):
    def __init__(self, parent, id=-1, dpi=None, **kwargs):
        wx.Panel.__init__(self, parent, id=id, **kwargs)
        self.parent = parent
        self.figure, self.ax = plt.subplots()
        self.lines = self.ax.plot(plotdata)
        self.ax.legend(['channel {}'.format(c) for c in range(nb_canaux)],
                    loc='lower left', ncol=nb_canaux)
        self.ax.axis((0, len(plotdata)/2, -1, 1))
        self.ax.yaxis.grid(True)
        self.figure.tight_layout(pad=0)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        self.SetSizer(sizer)
        return
        
    def DrawPage(self,evt):
        self.update_plot(None)
        return 

    def update_plot(self, frame):
        """This is called by matplotlib for each plot update.

        Typically, audio callbacks happen more frequently than plot updates,
        therefore the queue tends to contain multiple blocks of audio data.

        """
        global plotdata
        while True:
            try:
                data = q.get_nowait()
            except queue.Empty:
                break
            shift = len(data)
            plotdata = np.roll(plotdata, -shift, axis=0)
            plotdata[-shift:, :] = data
        for column, line in enumerate(self.lines):
            line.set_ydata((column+1) *plotdata[:, column])
        return self.lines


class PlotNotebook(wx.Panel):
    def __init__(self, parent, id=-1, evt_type=None):
        wx.Panel.__init__(self, parent, id=id)
        self.nb = aui.AuiNotebook(self)
        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        self.page = []
        self.SetSizer(sizer)
        self.parent =  parent
        self.Bind(evt_type, self.drawPage)
        self.clock = 0
        return

    def add(self, name="plot"):
        page =  Plot(self.nb)
        self.page.append(page)
        self.nb.AddPage(page, name)
        return page

    def drawPage(self, evt):
        if time.clock() - self.clock <0.10:
            return 
        self.clock = time.clock()
        for page in self.page:
            if self.nb.GetCurrentPage() == page:
                page.DrawPage(evt)
                page.canvas.draw()

