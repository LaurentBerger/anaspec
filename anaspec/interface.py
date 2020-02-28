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
        self.dico_label={0:('Enable','Disable',0)}
        self.ind_page = 0
        self.ajouter_page_acquisition()
        self.ajouter_page_tfd("Fourier")
        self.ajouter_page_spectrogram("Spectrogram")
        self.nb.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.close_page)
        frame = wx.Frame(None, -1, 'Mes Courbes',
                         style=wx.DEFAULT_FRAME_STYLE & (~wx.CLOSE_BOX) & (~wx.MAXIMIZE_BOX))
        plotter = fc.PlotNotebook(frame, 
                                  self.flux_audio,
                                  evt_type=self.EVT_SOME_NEW_EVENT)
        page1 = plotter.add('Time Signal', type_courbe='time')
        page2 = plotter.add('Spectral', type_courbe='dft_modulus')
        page3 = plotter.add('Spectrogram', type_courbe='spectrogram')
        self.flux_audio.courbe = plotter
        frame.Show()

    def close_page(self, evt):
        wx.MessageBox("Cannot be closed", "Warning", wx.ICON_WARNING)
        evt.Veto()

    def ajouter_page_tfd(self, name="Sampling"):
        ctrl = []
        page = wx.Panel(self.nb)
        font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_BOLD)
        ma_grille = wx.GridSizer(rows=3, cols=2, vgap=5, hgap=5)
        self.dico_label[2000]= ('Enable plot spectrum','Disable plot spectrum',self.ind_page)
        bouton = wx.Button(page, id=2000, label='Enable plot spectrum')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.OnEnableGraphic, bouton)
        self.ajouter_bouton((bouton,0), ctrl, ma_grille, font)

        st = wx.StaticText(page, label="")
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)
 
        st = wx.StaticText(page, label="Low frequency (Hz)")
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)

        st = wx.Slider(page, id=2001, value=0, minValue=0,
                       maxValue=self.flux_audio.Fe/2,
                       style=wx.SL_HORIZONTAL|wx.SL_LABELS|wx.SL_MIN_MAX_LABELS,
                       name="LowFrequency")
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)
        st.Bind(wx.EVT_SCROLL, self.change_fmin, st,2001)

        st = wx.StaticText(page, label="High frequency (Hz)")
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)

        st = wx.Slider(page, id=2002, value=self.flux_audio.Fe/2, minValue=0,
                       maxValue=self.flux_audio.Fe/2,
                       style=wx.SL_HORIZONTAL|wx.SL_LABELS|wx.SL_MIN_MAX_LABELS,
                       name="HighFrequency")
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)
        st.Bind(wx.EVT_SCROLL, self.change_fmax, st,2002)

        page.SetSizerAndFit(ma_grille)
        self.nb.AddPage(page, name)
        self.ctrl.append(ctrl)
        self.ind_page =  self.ind_page + 1


    def change_fmax(self, e):

        obj = e.GetEventObject()
        val = obj.GetValue()

        self.flux_audio.k_max = int(val / self.flux_audio.Fe * self.flux_audio.nb_ech_fenetre)
        self.flux_audio.courbe.etendue_axe(self.flux_audio.nb_ech_fenetre)

    def change_fmin(self, e):

        obj = e.GetEventObject()
        val = obj.GetValue()

        self.flux_audio.k_min = int(val / self.flux_audio.Fe * self.flux_audio.nb_ech_fenetre)
        self.flux_audio.courbe.etendue_axe(self.flux_audio.nb_ech_fenetre)


    def ajouter_page_acquisition(self, name="Sampling"):
        ctrl = []
        page = wx.Panel(self.nb)
        font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_BOLD)
        ma_grille = wx.GridSizer(rows=4, cols=2, vgap=5, hgap=5)
        self.dico_label[1000]= ('Start','Stop')
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
        self.ind_page = self.ind_page + 1

    def ajouter_page_spectrogram(self, name="Spectrogram"):
        ctrl = []
        page = wx.Panel(self.nb)
        font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_BOLD)
        ma_grille = wx.GridSizer(rows=3, cols=2, vgap=5, hgap=5)
        self.dico_label[3000]= ('Enable spectrogram','Disable spectrogram',self.ind_page)
        bouton = wx.Button(page, id=3000, label='Enable spectrogram')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.OnEnableGraphic, bouton)
        self.ajouter_bouton((bouton,0), ctrl, ma_grille, font)

        st = wx.StaticText(page, label="")
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)
 
        st = wx.StaticText(page, label="Low frequency (Hz)")
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)

        st = wx.Slider(page, id=3001, value=0, minValue=0,
                       maxValue=self.flux_audio.Fe/2,
                       style=wx.SL_HORIZONTAL|wx.SL_LABELS|wx.SL_MIN_MAX_LABELS,
                       name="LowFrequency")
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)
        st.Bind(wx.EVT_SCROLL, self.change_fmin, st,3001)

        st = wx.StaticText(page, label="High frequency (Hz)")
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)

        st = wx.Slider(page, id=3002, value=self.flux_audio.Fe/2, minValue=0,
                       maxValue=self.flux_audio.Fe/2,
                       style=wx.SL_HORIZONTAL|wx.SL_LABELS|wx.SL_MIN_MAX_LABELS,
                       name="HighFrequency")
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)
        st.Bind(wx.EVT_SCROLL, self.change_fmax, st,3002)

        page.SetSizerAndFit(ma_grille)
        self.nb.AddPage(page, name)
        self.ctrl.append(ctrl)
        self.ind_page =  self.ind_page + 1


    def ajouter_bouton(self, bt, ctrl, ma_grille, font):
        bt[0].SetFont(font)
        ctrl.append(bt)
        ma_grille.Add(bt[0],0, wx.EXPAND)

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

    def OnEnableGraphic(self, event):

        bouton = event.GetEventObject()
        id = event.GetId()
        if id not in self.dico_label:
            return
        couleur =  bouton.GetBackgroundColour()
        ind_page = self.dico_label[id][2]
        if couleur[1] == 255:
            bouton.SetBackgroundColour(wx.Colour(255, 0, 0))
            bouton.SetLabel(self.dico_label[id][1])
            self.flux_audio.courbe.page[ind_page].courbe_active = True
        else:
            bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
            bouton.SetLabel(self.dico_label[id][0])
            self.flux_audio.courbe.page[ind_page].courbe_active = False


    def OnStartStop(self, event):

        bouton = event.GetEventObject()
        s = bouton.GetLabel()
        if s == "Start":
            self.set_frequency()
            self.set_window_size()
            self.set_time_length()
            self.flux_audio.courbe.etendue_axe(self.flux_audio.nb_ech_fenetre)
            self.flux_audio.open()
            self.flux_audio.courbe.page[0].courbe_active = True
            bouton.SetLabel("Stop")
            bouton.SetBackgroundColour(wx.Colour(255, 0, 0))
            self.figer_parametre(True)
        else:
            self.flux_audio.close()
            self.flux_audio.courbe.page[0].courbe_active = False
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

