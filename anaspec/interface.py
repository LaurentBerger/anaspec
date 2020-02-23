import os
import wx
import wx.lib.agw.aui as aui
import fluxaudio
import fenetrecourbe as fc

class InterfaceAnalyseur(wx.Panel):
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self, parent, id=id)
        self.nb = aui.AuiNotebook(self, style=aui.AUI_NB_TOP | aui.AUI_NB_TAB_SPLIT |
                                  aui.AUI_NB_TAB_MOVE | aui.AUI_NB_MIDDLE_CLICK_CLOSE)
        
        self.new_event, self.EVT_SOME_NEW_EVENT = wx.lib.newevent.NewEvent()
        self.flux_audio = fluxaudio.FluxAudio(self.new_event)

        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.ctrl = []
        self.ajouter_page_acquisition()
        self.nb.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.close_page)
        frame = wx.Frame(None, -1, 'Mes Courbes',style=wx.DEFAULT_FRAME_STYLE & (~wx.CLOSE_BOX) & (~wx.MAXIMIZE_BOX))
        plotter = fc.PlotNotebook(frame, 
                                  self.flux_audio,
                                  evt_type=self.EVT_SOME_NEW_EVENT)
        page1 = plotter.add('figure 1')
        self.flux_audio.courbe = plotter
        frame.Show()

    def close_page(self, evt):
        wx.MessageBox("Cannot be closed", "Warning", wx.ICON_WARNING)
        evt.Veto()

    def ajouter_page_acquisition(self, name="Sampling"):
        ctrl = []
        page = wx.Panel(self.nb)
        font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_BOLD)
        ma_grille = wx.GridSizer(rows=4, cols=2, vgap=5, hgap=5)
        bouton = wx.Button(page, id=1000, label='Start')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.OnStartStop, bouton)
        self.ajouter_bouton((bouton,0), ctrl, ma_grille, font)

        st = wx.StaticText(page, label="")
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)
 
        st = wx.StaticText(page, label="frequency")
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)

        st = wx.TextCtrl(page, value=str(self.flux_audio.Fe))
        self.ajouter_bouton((st,1), ctrl, ma_grille, font)

        st = wx.StaticText(page, label="recording Time (-1 for infinite)")
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)

        st = wx.TextCtrl(page, value="-1", id=1001)
        self.ajouter_bouton((st,1), ctrl, ma_grille, font)

        st = wx.StaticText(page, label="# sampling per window ")
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)

        st = wx.TextCtrl(page, value=str(self.flux_audio.nb_ech_fenetre), id=1002)
        self.ajouter_bouton((st,1), ctrl, ma_grille, font)

        page.SetSizerAndFit(ma_grille)
        self.nb.AddPage(page, name)
        self.ctrl.append(ctrl)

    def ajouter_bouton(self, bt, ctrl, ma_grille, font):
        bt[0].SetFont(font)
        ctrl.append(bt)
        ma_grille.Add(bt[0])

    def set_frequency(self):
        s = self.ctrl[0][3][0].GetValue()
        freq = int(s)
        if freq>0:
            self.flux_audio.Fe = freq
            return freq
        return None

    def set_window_size(self):
        s = self.ctrl[0][7][0].GetValue()
        nb_ech_fenetre = int(s)
        if nb_ech_fenetre>0:
            self.flux_audio.nb_ech_fenetre = nb_ech_fenetre
            self.flux_audio.init_data_courbe()
            return nb_ech_fenetre
        return None

    def set_time_length(self):
        s = self.ctrl[0][5][0].GetValue()
        duration = int(s)
        self.duration = -1

    def OnStartStop(self, event):

        bouton = event.GetEventObject()
        s = bouton.GetLabel()
        if s == "Start":
            self.set_frequency()
            self.set_window_size()
            self.set_time_length()
            self.flux_audio.courbe.etendue_axe(self.flux_audio.nb_ech_fenetre)
            self.flux_audio.open()
            bouton.SetLabel("Stop")
            bouton.SetBackgroundColour(wx.Colour(255, 0, 0))
            self.figer_parametre(True)
        else:
            self.flux_audio.close()
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
    application = wx.App()
    frame = wx.Frame(None, -1, 'Interface')
    plotter = InterfaceAnalyseur(frame)
    frame.Show()
    application.MainLoop()

