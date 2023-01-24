import wx.grid


class GridFrequency(wx.Frame):
    def __init__(self, parent,pos=(0,280), nb_rows=100, nb_cols=10):
        wx.Frame.__init__(self, parent,title="Marker values", pos=pos, size=(660,520))

        # Create a wxGrid object
        self.grid = wx.grid.Grid(self, -1)
        self.nb_rows = nb_rows
        self.nb_cols = nb_cols
        # Then we call CreateGrid to set the dimensions of the grid
        # (100 rows and 10 columns in this example)
        self.grid.CreateGrid(nb_rows, nb_cols)
 
        # We can set the sizes of individual rows and columns
        # in pixels
        self.Show()
        self.Bind(wx.EVT_CLOSE, self.close_page)
        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.line_selected)
        self.peak = False
        self.oscilloscope = None

    def close_page(self, evt):
        self.Show(False)
        evt.Veto()

    def line_selected(self, evt):
        if evt.GetRow() != -1:
            self.grid.SetSelectionMode(wx.grid.Grid.GridSelectRows)
            self.grid.SelectRow(evt.GetRow())
            if self.oscilloscope is not None:
                freq = self.grid.GetCellValue(evt.GetRow(), 0)
                amplitude = self.grid.GetCellValue(evt.GetRow(), 1)
                if freq != "" and amplitude != "":
                    try:
                        f = float(freq)
                        a = float(amplitude)
                        self.oscilloscope.draw_circle(f, a)
                    except ValueError:
                        self.oscilloscope.clear_circle()
                else:
                    self.oscilloscope.clear_circle()
        if evt.GetCol() != -1:
            self.grid.SetSelectionMode(wx.grid.Grid.GridSelectColumns)
            self.grid.SelectCol(evt.GetCol())
 
    def set_oscilloscope(self, oscillo):
        self.oscilloscope =  oscillo

    def message(self, texte, peak=False):
        self.grid.ClearGrid()
        self.peak = peak
        ligne =  texte.split("\n")
        row = 0
        for row, val in enumerate(ligne):
            l_cell = val.split('\t')
            col = 0
            if row < self.nb_rows:
                for col, cell in enumerate(l_cell):
                    if col < self.nb_cols: 
                        self.grid.SetCellValue(row, col, cell)
