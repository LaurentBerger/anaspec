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
        self.parent = parent
        self.idmenu_audio_in = {-1:-1}
        self.idmenu_audio_out = {-1:-1}
        self.idx_periph_in = None
        self.idx_periph_out = None
        self.dico_slider = None
        self.flux_audio = fluxaudio.FluxAudio(self.new_event)
        self.install_menu()
        self.parent.Show()

    def select_audio_in(self,event):
        obj = event.GetEventObject()
        if self.idx_periph_in is None:
            self.interface_acquisition()
        l = obj.GetMenuItems()
        for art in l:
            art.Check(False)
        id = event.GetId()
        obj.Check(id,True)
        nom_periph_in = obj.GetLabel(id)
        if nom_periph_in in self.idmenu_audio_in:
            self.idx_periph_in = self.idmenu_audio_in[nom_periph_in]

    def disable_item_check(self):
        barre_menu = self.parent.GetMenuBar()
        menu = barre_menu.GetMenu(1)
        l = menu.GetMenuItems()
        for art in l:
            art.Check(False)
            if self.idmenu_audio_in[art.GetItemLabelText()] == self.idx_periph_in:
                art.Enable(False)

    def select_audio_out(self, event):
        pass

    def interface_acquisition(self):
        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.ctrl = []
        self.dico_label = {0:('Enable', 'Disable', 0)}
        self.dico_slider = {0:None}
        self.ind_page = 0
        self.ajouter_page_acquisition()
        self.ajouter_page_tfd("Fourier")
        self.ajouter_page_spectrogram("Spectrogram")
        self.nb.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.close_page)
        self.nb.Refresh(True)
        self.nb.SetSize(self.parent.GetClientSize())
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

    def install_menu(self):
        self.liste_periph = self.flux_audio.get_device()
        self.idmenu_audio_in = {-1:-1}
        self.idmenu_audio_in = {x['name']:idx 
                                for idx,x in enumerate(self.liste_periph) 
                                if x['max_input_channels'] >= 1}
        self.idmenu_audio_out = {-1:-1}
        self.idmenu_audio_out = {x['name']:idx for idx,x in enumerate(self.liste_periph) if x['max_output_channels'] >= 1}
        barre_menu = wx.MenuBar()
        menu_fichier = wx.Menu()
        article_quitter = menu_fichier.Append(wx.ID_EXIT, 'Quit', "exit program")
        barre_menu.Append(menu_fichier, '&File')
        menu_file = wx.Menu()
        menu_periph_in = wx.Menu()
        self.idmenu_perih = {-1:-1}
        [menu_periph_in.AppendCheckItem(idx+200,x) for idx,x in enumerate(self.idmenu_audio_in)]
        barre_menu.Append(menu_periph_in,'input device')
        menu_periph_out = wx.Menu()
        [menu_periph_out.AppendCheckItem(idx+300,x) for idx,x in enumerate(self.idmenu_audio_out)]
        barre_menu.Append(menu_periph_out,'output device')
        menu_about = wx.Menu()
        article_about = menu_about.Append(wx.ID_ABOUT, 'About', 'About anaspec')
        barre_menu.Append(menu_about, '&Help')
        self.parent.SetMenuBar(barre_menu)
        self.parent.Bind(wx.EVT_MENU, self.select_audio_in,id=200,id2=299)
        self.parent.Bind(wx.EVT_MENU, self.select_audio_out,id=300,id2=399)

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
        st.Bind(wx.EVT_SCROLL, self.change_slider, st,2001)
        self.dico_slider[2001] = self.flux_audio.set_k_min

        st = wx.StaticText(page, label="High frequency (Hz)")
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)

        st = wx.Slider(page, id=2002, value=self.flux_audio.Fe/2, minValue=0,
                       maxValue=self.flux_audio.Fe/2,
                       style=wx.SL_HORIZONTAL|wx.SL_LABELS|wx.SL_MIN_MAX_LABELS,
                       name="HighFrequency")
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)
        st.Bind(wx.EVT_SCROLL, self.change_slider, st,2002)
        self.dico_slider[2002] = self.flux_audio.set_k_max

        page.SetSizerAndFit(ma_grille)
        self.nb.AddPage(page, name)
        self.ctrl.append(ctrl)
        self.ind_page =  self.ind_page + 1

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
        ma_grille = wx.GridSizer(rows=6, cols=2, vgap=5, hgap=5)
        self.dico_label[3000]= ('Enable spectrogram','Disable spectrogram',self.ind_page)
        bouton = wx.Button(page, id=3000, label='Enable spectrogram')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.OnEnableGraphic, bouton)
        self.ajouter_bouton((bouton,0), ctrl, ma_grille, font)

        st = wx.StaticText(page, label="")
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)
 
        st = wx.StaticText(page, label="Low frequency (Hz)")
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)

        st = wx.Slider(page, id=3001, value=self.flux_audio.f_min_spectro, minValue=0,
                       maxValue=self.flux_audio.Fe/2,
                       style=wx.SL_HORIZONTAL|wx.SL_LABELS|wx.SL_MIN_MAX_LABELS,
                       name="LowFrequency")
        self.dico_slider[3001] = self.flux_audio.set_f_min_spectro
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)
        st.Bind(wx.EVT_SCROLL, self.change_slider, st,3001)

        st = wx.StaticText(page, label="High frequency (Hz)")
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)

        st = wx.Slider(page, id=3002, value=self.flux_audio.f_max_spectro, minValue=0,
                       maxValue=self.flux_audio.Fe/2,
                       style=wx.SL_HORIZONTAL|wx.SL_LABELS|wx.SL_MIN_MAX_LABELS,
                       name="HighFrequency")
        self.dico_slider[3002] = self.flux_audio.set_f_max_spectro
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)
        st.Bind(wx.EVT_SCROLL, self.change_slider, st,3002)

        st = wx.StaticText(page, label="Window size")
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)

        st = wx.Slider(page, id=3003, value=self.flux_audio.win_size_spectro, minValue=0,
                       maxValue=self.flux_audio.nb_ech_fenetre,
                       style=wx.SL_HORIZONTAL|wx.SL_LABELS|wx.SL_MIN_MAX_LABELS,
                       name="WindowSize")
        st.Bind(wx.EVT_SCROLL, self.change_slider, st,3003)
        self.dico_slider[3003] = self.flux_audio.set_win_size_spectro
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)

        st = wx.StaticText(page, label="Overlap")
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)

        st = wx.Slider(page, id=3004, value=self.flux_audio.overlap_spectro, minValue=0,
                       maxValue=self.flux_audio.nb_ech_fenetre-1,
                       style=wx.SL_HORIZONTAL|wx.SL_LABELS|wx.SL_MIN_MAX_LABELS,
                       name="Overlap")
        self.dico_slider[3004] = self.flux_audio.set_overlap_spectro
        st.Bind(wx.EVT_SCROLL, self.change_slider, st,3004)
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)

        st = wx.StaticText(page, label="Window")
        self.ajouter_bouton((st,0), ctrl, ma_grille, font)
        type_window = ['boxcar', 'triang', 'blackman', 'hamming', 'hann',
                       'bartlett', 'flattop', 'parzen', 'bohman', 'blackmanharris',
                       'nuttall', 'barthann', 'kaiser', 'gaussian','general_gaussian',
                       'slepian', 'dpss', 'chebwin', 'exponential', 'tukey']
        st = wx.ComboBox(page,id=3005, choices=type_window)
        self.ajouter_bouton((st,0), ctrl, ma_grille, font, wx.Centre)
        page.SetSizerAndFit(ma_grille)
        self.nb.AddPage(page, name)
        self.ctrl.append(ctrl)
        self.ind_page =  self.ind_page + 1

    def change_slider(self, event):
        obj = event.GetEventObject()
        val = obj.GetValue()
        id = event.GetId()
        if id not in self.dico_slider:
            return
        self.dico_slider[id](val)
        self.flux_audio.courbe.etendue_axe(self.flux_audio.nb_ech_fenetre)

    def update_spectro_interface(self):
        low = wx.Window.FindWindowById(3001)
        if low:
            low.SetMax(self.flux_audio.Fe/2)
        high = wx.Window.FindWindowById(3002)
        if high:
            high.SetMax(self.flux_audio.Fe/2)
        win_size = wx.Window.FindWindowById(3003)
        if win_size:
            win_size.SetMax(self.flux_audio.nb_ech_fenetre)
        overlap = wx.Window.FindWindowById(3004)
        if overlap:
            overlap.SetMax(self.flux_audio.nb_ech_fenetre-1)


    def ajouter_bouton(self, bt, ctrl, ma_grille, font, option=wx.EXPAND):
        bt[0].SetFont(font)
        ctrl.append(bt)
        ma_grille.Add(bt[0],0, option)

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
            self.update_spectro_interface()
            bouton.SetBackgroundColour(wx.Colour(255, 0, 0))
            bouton.SetLabel(self.dico_label[id][1])
            self.flux_audio.courbe.page[ind_page].courbe_active = True
        else:
            bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
            bouton.SetLabel(self.dico_label[id][0])
            self.flux_audio.courbe.page[ind_page].courbe_active = False


    def OnStartStop(self, event):

        if self.idmenu_audio_in is None:
            wx.MessageBox("You must select an audio in device", "Warning", wx.ICON_WARNING)
        bouton = event.GetEventObject()
        s = bouton.GetLabel()
        if s == "Start":
            self.set_frequency()
            self.set_window_size()
            self.set_time_length()
            self.flux_audio.courbe.etendue_axe(self.flux_audio.nb_ech_fenetre)
            if not self.flux_audio.open(self.idx_periph_in):
                self.disable_item_check()
                wx.MessageBox("Cannot opened input device : input disable", "Error", wx.ICON_WARNING)
                return
            self.update_spectro_interface()
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

