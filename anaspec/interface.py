import os
import wx
import wx.lib.agw.aui as aui

class InterfaceAnalyseur(wx.Panel):
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id=id)
        self.nb = aui.AuiNotebook(self, style= aui.AUI_NB_TOP | aui.AUI_NB_TAB_SPLIT |
                                 aui.AUI_NB_TAB_MOVE | aui.AUI_NB_MIDDLE_CLICK_CLOSE)
        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.ctrl = []
        self.ajouter_page_acquisition()
        self.nb.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE,self.close_page)

    def close_page(self, evt):
        wx.MessageBox("Cannot be closed", "Warning", wx.ICON_WARNING)
        evt.Veto()


    def ajouter_page_acquisition(self, name="Sampling"):
        ctrl = []
        page = wx.Panel(self.nb)
        font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
            wx.FONTWEIGHT_BOLD)
        ma_grille = wx.GridSizer(rows=4, cols= 2, vgap=5, hgap=5)
        bouton = wx.Button(page, id=1000, label='Start')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.OnStartStop, bouton)
        bouton.SetFont(font)
        ctrl.append((bouton,0))
        ma_grille.Add(bouton, 1, wx.EXPAND)
        st = wx.StaticText(page, label="")
        ctrl.append((st,0))
        ma_grille.Add(st)

        st = wx.StaticText(page, label="frequency")
        ctrl.append((st,0))
        ma_grille.Add(st)

        st = wx.StaticText(page, label="")
        ctrl.append((st,1))
        ma_grille.Add(st)

        st = wx.StaticText(page, label="recording Time (-1 for infinite)")
        ctrl.append((st,0))
        ma_grille.Add(st)

        st = wx.TextCtrl(page, value="-1", id=1001)
        ctrl.append((st,1))
        ma_grille.Add(st)

        st = wx.StaticText(page, label="# sampling per window ")
        ctrl.append((st,0))
        ma_grille.Add(st)
        
        st = wx.TextCtrl(page, value="1024", id=1002)
        ctrl.append((st,1))
        ma_grille.Add(st)

        page.SetSizerAndFit(ma_grille) 
        self.nb.AddPage(page, name)
        self.ctrl.append(ctrl)

    def OnStartStop(self, event):
        bouton = event.GetEventObject()
        s = bouton.GetLabel()
        if s == "Start":
            bouton.SetLabel("Stop")
            bouton.SetBackgroundColour(wx.Colour(255, 0, 0))
            self.figer_parametre(True)
        else:
            bouton.SetLabel("Start")
            bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
            self.figer_parametre(False)

    def figer_parametre(self, enable):
        for l in self.ctrl:
            for ctrl in l:
                if ctrl[1]:
                    if enable:
                        ctrl[0].Disable()
                    else:
                        ctrl[0].Enable()

       
if __name__ == '__main__':
    app = wx.App()
    frame = wx.Frame(None, -1, 'Interface')
    plotter = InterfaceAnalyseur(frame)
    frame.Show()
    app.MainLoop()

