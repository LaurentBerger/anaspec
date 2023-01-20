import wx.grid

class GridFrequency(wx.Frame):
    def __init__(self, parent, nb_rows=100, nb_cols=10):
        wx.Frame.__init__(self, parent)

        # Create a wxGrid object
        self.grid = wx.grid.Grid(self, -1)

        # Then we call CreateGrid to set the dimensions of the grid
        # (100 rows and 10 columns in this example)
        self.grid.CreateGrid(nb_rows, nb_cols)

        # We can set the sizes of individual rows and columns
        # in pixels
        self.Show()
        self.Bind(wx.EVT_CLOSE, self.close_page)

    def close_page(self, evt):
        self.Show(False)
        evt.Veto()

    def message(self, texte):
        ligne =  texte.split("\n")
        row = 0
        for row, val in enumerate(ligne):
            l_cell = val.split('\t')
            col = 0
            for col, cell in enumerate(l_cell):
                self.grid.SetCellValue(row, col, cell)
