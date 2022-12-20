"""
Interface de l'analyseur :
réglages des paramètres d'acquisition
pour la tfd, sélection de la bande de fréquence pour l'affichage
pour le spectrogramme, sélection de la bande de fréquence, du nombre
d'échantillon, du recouvrement, du type de fenêtrage
"""
# pylint: disable=maybe-no-member
import sys
import soundfile
import sounddevice as sd
import wx
import wx.lib.agw.aui as aui
import fluxaudio
import fenetrecourbe as fc

MIN_TFD_SIZE = 256
MIN_SPECTRO_SIZE = 256

SAVE_SIGNAL = 1001
START_SAMPLING = 1002
RECORDING_TIME = 1003
UPDATE_ECH = 1004

SLIDER_F_MIN_TFD = 2001
SLIDER_F_MAX_TFD = 2002
SLIDER_TFD_SIZE = 2003

SLIDER_F_MIN_SPECTRO = 3001
SLIDER_F_MAX_SPECTRO = 3002
SLIDER_WINDOW_SIZE_SPECTRO = 3003
SLIDER_OVERLAP_SPECTRO = 3004
SLIDER_SPECTRO_SIZE = 3005
COMBO_WINDOW_TYPE = 3006




PARAM1_WINDOW_TYPE = COMBO_WINDOW_TYPE + 2
PARAM2_WINDOW_TYPE = PARAM1_WINDOW_TYPE + 2


class InterfaceAnalyseur(wx.Panel):
    """
    onglets pour les réglages de l'acquisition,
    pour les réglages de l'affichage de la tfd,
    pour les réglages de l'affichage du spectrogramme
    """
    def __init__(self, parent, id_fenetre=-1):
        """
        membre :
        parent : fenêtre parent
        note_book : contient les onglets signal, tfd et spectrogramme
        new_event : évènement pour la gestion du temps réel
        idmenu_audio_in  : dictionnaire idmenu audio-in vers
        index du périphérique audio dans liste des périphériques
        idmenu_audio_out : dictionnaire idmenu audio-out vers
        index du périphérique audio dans liste des périphériques
        idx_periph_in : indice du périphérique d'entré sélectionné
                        dans liste des périphériques
        idx_periph_out : indice du périphérique de sortie sélectionné
                         dans liste des périphériques
        dico_slider : dictionnaire idslider vers fonction modifiant la valeur
                      glissières
        flux_audio : périphérique audio en entrée ouvert
        type_window : fenêtre pour la tfd et le spectrogramme
        dico_window : fenêtre et nombre de paramètre utilisée
                      pour définir la fenêtre
        """
        wx.Panel.__init__(self, parent, id=id_fenetre)
        self.note_book = aui.AuiNotebook(self,
                                         style=aui.AUI_NB_TOP |
                                         aui.AUI_NB_TAB_SPLIT |
                                         aui.AUI_NB_TAB_MOVE |
                                         aui.AUI_NB_MIDDLE_CLICK_CLOSE)

        self.new_event, self.id_evt = wx.lib.newevent.NewEvent()
        self.parent = parent
        self.init_interface = False
        self.idmenu_audio_in = {-1: -1}
        self.idmenu_audio_out = {-1: -1}
        self.idx_periph_in = None
        self.idx_periph_out = None
        self.dico_slider = None
        self.dico_label = None
        self.ctrl = None
        self.ind_fichier = 0
        self.ind_page = 0
        self.duration = -1
        self.flux_audio = fluxaudio.FluxAudio(self.new_event)
        self.install_menu()
        self.parent.Show()
        self.type_window = ['boxcar', 'triang', 'blackman', 'hamming',
                            'hann', 'bartlett', 'flattop', 'parzen',
                            'bohman', 'blackmanharris', 'nuttall', 'barthann',
                            'kaiser', 'gaussian', 'general_gaussian',
                            'slepian', 'dpss', 'chebwin', 'exponential',
                            'tukey']
        self.dico_window = {'boxcar': (None),
                            'triang': (None),
                            'blackman': (None),
                            'hamming': (None),
                            'hann': (None),
                            'bartlett': (None),
                            'flattop': (None),
                            'parzen': (None),
                            'bohman': (None),
                            'blackmanharris': (None),
                            'nuttall': (None),
                            'barthann': (None),
                            'kaiser': ('beta', None),
                            'gaussian': ('std', None),
                            'general_gaussian': ('p', 'sig', None),
                            'slepian': ('bandwidth', None),
                            'dpss': ('NW', 'Kmax', 'norm', None),
                            'chebwin': ('at', None),
                            'exponential': ('tau', None),
                            'tukey': ('alpha', None)}
        self.flux_audio.type_window = self.type_window[0]
        self.choix_freq =  None # liste de choix pour les fréquences
        self.samp_in_progress = False

    def select_audio_in(self, event):
        """
        fonction appelée lorsqu'un périphérique
        est sélectionné dans le menu audio_in :
        activation de l'interface d'acquisition et
        ajout d'une marque sur l'article sélectionné
        """
        obj = event.GetEventObject()
        self.disable_item_check(1)
        id_fenetre = event.GetId()
        obj.Check(id_fenetre, True)
        nom_periph_in = obj.GetLabel(id_fenetre)
        if nom_periph_in in self.idmenu_audio_in:
            self.idx_periph_in = self.idmenu_audio_in[nom_periph_in]
            self.flux_audio.nb_canaux = self.liste_periph[self.idx_periph_in]["max_input_channels"]
            self.flux_audio.nb_canaux = self.liste_periph[self.idx_periph_in]["max_input_channels"]
            self.flux_audio.set_frequency(self.liste_periph[self.idx_periph_in]["default_samplerate"])
            self.flux_audio.capacite_periph_in(self.liste_periph, self.idx_periph_in)
            self.flux_audio.init_data_courbe()
        if not self.init_interface:
            self.interface_acquisition()
            self.init_interface = True
        if self.choix_freq is not None:
            self.maj_choix_freq()

    def disable_item_check(self, indexe=1):
        """
        enlève les marques du menu en position
        indexe dans la barre de menu
        """
        barre_menu = self.parent.GetMenuBar()
        menu = barre_menu.GetMenu(indexe)
        liste_art = menu.GetMenuItems()
        for art in liste_art:
            art.Check(False)

    def select_audio_out(self, event):
        """
        fonction appelée lorsqu'un périphérique
        est sélectionné dans le menu audio_out :
        activation de l'interface d'acquisition et
        ajout d'une marque sur l'article sélectionné
        """
        obj = event.GetEventObject()
        self.disable_item_check(2)
        id_fenetre = event.GetId()
        obj.Check(id_fenetre, True)
        nom_periph_out = obj.GetLabel(id_fenetre)
        if nom_periph_out in self.idmenu_audio_out:
            self.idx_periph_out = self.idmenu_audio_out[nom_periph_out]
            sd.default.device[1] = self.idx_periph_out

    def interface_acquisition(self):
        """
        Mise en place de l'interface d'acquisition
        pour le signal temporel, la tfd et le spectrogramme
        """
        sizer = wx.BoxSizer()
        sizer.Add(self.note_book, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.ctrl = []
        self.dico_label = {0: ('Enable', 'Disable', 0)}
        self.dico_slider = {0: None}
        self.ind_page = 0
        self.ajouter_page_acquisition()
        self.ajouter_page_tfd("Fourier")
        self.ajouter_page_spectrogram("Spectrogram")
        self.note_book.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.close_page)
        self.note_book.Refresh(True)
        self.note_book.SetSize(self.parent.GetClientSize())
        frame = wx.Frame(None, -1,
                         'Mes Courbes',
                         style=wx.DEFAULT_FRAME_STYLE &
                         (~wx.CLOSE_BOX) &
                         (~wx.MAXIMIZE_BOX))
        plotter = fc.PlotNotebook(frame,
                                  self.flux_audio,
                                  evt_type=self.id_evt)
        _ = plotter.add('Time Signal', type_courbe='time')
        _ = plotter.add('Spectral', type_courbe='dft_modulus')
        _ = plotter.add('Spectrogram', type_courbe='spectrogram')
        self.flux_audio.courbe = plotter

        frame.Show()

    def install_menu(self):
        """
        Installation des menus
        """
        self.liste_periph = self.flux_audio.get_device()
        self.idmenu_audio_in = {-1: -1}
        self.idmenu_audio_in = {x['name']: idx
                                for idx, x in enumerate(self.liste_periph)
                                if x['max_input_channels'] >= 1}
        self.idmenu_audio_out = {-1: -1}
        self.idmenu_audio_out = {x['name']: idx
                                 for idx, x in enumerate(self.liste_periph)
                                 if x['max_output_channels'] >= 1}
        barre_menu = wx.MenuBar()
        menu_fichier = wx.Menu()
        _ = menu_fichier.Append(wx.ID_OPEN, 'Open', "open wave file")
        _ = menu_fichier.Append(wx.ID_SAVE, 'Save', "save wave file")
        _ = menu_fichier.Append(wx.ID_EXIT, 'Quit', "exit program")
        barre_menu.Append(menu_fichier, '&File')
        _ = wx.Menu()
        menu_periph_in = wx.Menu()
        self.idmenu_perih = {-1: -1}
        _ = [menu_periph_in.AppendCheckItem(idx+200, x)
             for idx, x in enumerate(self.idmenu_audio_in)]
        barre_menu.Append(menu_periph_in, 'input device')
        menu_periph_out = wx.Menu()
        _ = [menu_periph_out.AppendCheckItem(idx+300, x)
             for idx, x in enumerate(self.idmenu_audio_out)]
        barre_menu.Append(menu_periph_out, 'output device')
        menu_about = wx.Menu()
        _ = menu_about.Append(wx.ID_ABOUT, 'About', 'About anaspec')
        barre_menu.Append(menu_about, '&Help')
        self.parent.SetMenuBar(barre_menu)
        self.parent.Bind(wx.EVT_CLOSE, self.close_page)
        self.parent.Bind(wx.EVT_MENU, self.open_wav, id=wx.ID_OPEN)
        self.parent.Bind(wx.EVT_MENU, self.on_save, id=wx.ID_SAVE)
        self.parent.Bind(wx.EVT_MENU, self.quitter, id=wx.ID_EXIT)
        self.parent.Bind(wx.EVT_MENU, self.select_audio_in, id=200, id2=299)
        self.parent.Bind(wx.EVT_MENU, self.select_audio_out, id=300, id2=399)

    def close_page(self, evt):
        """
        surchage de close pour interdire
        la fermeture des onglets
        """
        wx.MessageBox("Cannot be closed. Use File menu to quit", "Warning", wx.ICON_WARNING)
        evt.Veto()

    def open_wav(self, _):
        """
        ouvrir un fichier wav et utilisé les données 
        de la même manière que l'acquisition
        """
        if self.flux_audio.plotdata is None:
               wx.MessageBox("First choose peripherical in input device menu", "Error", wx.ICON_ERROR)
               return
        nom_fichier_son = wx.FileSelector("Open wave file",wildcard="*.wav")
        if nom_fichier_son.strip():
            self.set_window_size()
            son , Fe = soundfile.read(nom_fichier_son)
            if self.flux_audio.Fe != Fe:
                wx.MessageBox("Sampling frequency are not equal\n "+ str(self.flux_audio.Fe) + "Hz<> " +str(Fe), "Error", wx.ICON_ERROR)
                return
            nb_ech = min(son.shape[0], self.flux_audio.plotdata.shape[0])
            self.flux_audio.courbe.page[0].t_beg = self.flux_audio.plotdata.shape[0] - nb_ech
            self.flux_audio.courbe.page[0].t_end = self.flux_audio.taille_buffer_signal
            self.flux_audio.courbe.page[0].maj_limite_slider()
            if len(son.shape) == 1:
                self.flux_audio.plotdata[self.flux_audio.plotdata.shape[0] - nb_ech:,0] += son[:nb_ech]
            else:
                self.flux_audio.plotdata[self.flux_audio.plotdata.shape[0] - nb_ech:,0] += son[:nb_ech,0]
                if son.shape[1] != self.flux_audio.plotdata.shape[1]:
                    wx.MessageBox("Channel number are not equal. First channel uses", "Warning", wx.ICON_WARNING)
                elif son.shape[1] == 2:
                    self.flux_audio.plotdata[self.flux_audio.plotdata.shape[0]-nb_ech:,1] += son[:nb_ech,1] 
            # self.flux_audio.nb_ech_fenetre = nb_ech 
            # wx.MessageBox("Update sampling modified\n New value "+str(nb_ech), "Warning", wx.ICON_WARNING)
            # w = wx.Window.FindWindowById(UPDATE_ECH)
            # w.SetLabel(str(self.flux_audio.nb_ech_fenetre))
            self.flux_audio.courbe.page[0].courbe_active = True
            self.flux_audio.courbe.draw_all_axis()
            # self.flux_audio.courbe.draw_page(None)

    def quitter(self, _):
        """
        libérer ressource et quitter
        """
        sys.exit()

    def ajouter_page_tfd(self, name="Fourier"):
        """
        création de l'onglet Fourier
        pour paramétrer la tfd
        """
        ctrl = []
        page = wx.Panel(self.note_book)
        font = wx.Font(10,
                       wx.FONTFAMILY_DEFAULT,
                       wx.FONTSTYLE_NORMAL,
                       wx.FONTWEIGHT_BOLD)
        ma_grille = wx.GridSizer(rows=5, cols=2, vgap=5, hgap=5)
        self.dico_label[2000] = ('Enable plot spectrum',
                                 'Disable plot spectrum',
                                 self.ind_page)
        
        bouton = wx.Button(page, id=2000, label='Enable plot spectrum')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.on_enable_graphic, bouton)
        self.ajouter_bouton((bouton, 0), ctrl, ma_grille, font)
        st_texte = wx.StaticText(page, label="")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)

        """        
        st_texte = wx.StaticText(page, label="TFD size",)
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)
        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        min_v = self.flux_audio.set_tfd_size()
        st_texte = wx.Slider(page,
                             id=SLIDER_TFD_SIZE,
                             value=min_v,
                             minValue=MIN_TFD_SIZE,
                             maxValue=self.flux_audio.taille_buffer_signal,
                             style=style_texte,
                             name="SIZE_TFD")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)
        st_texte.Bind(wx.EVT_SCROLL,
                      self.change_tfd_size,
                      st_texte,
                      SLIDER_TFD_SIZE)
        self.dico_slider[SLIDER_TFD_SIZE] =(self.flux_audio.set_tfd_size, 'dft_modulus')
        """

        st_texte = wx.StaticText(page, label="Low frequency (Hz)")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)
        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        st_texte = wx.Slider(page,
                             id=SLIDER_F_MIN_TFD,
                             value=0,
                             minValue=0,
                             maxValue=int(self.flux_audio.set_frequency()//2),
                             style=style_texte,
                             name="LowFrequency")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)
        st_texte.Bind(wx.EVT_SCROLL_CHANGED,
                      self.change_slider,
                      st_texte,
                      SLIDER_F_MIN_TFD)
        self.dico_slider[SLIDER_F_MIN_TFD] = (self.flux_audio.set_f_min, 'dft_modulus')

        st_texte = wx.StaticText(page, label="High frequency (Hz)")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)
        st_texte = wx.Slider(page,
                             id=SLIDER_F_MAX_TFD,
                             value=int(self.flux_audio.set_frequency()//2),
                             minValue=0,
                             maxValue=int(self.flux_audio.set_frequency()//2),
                             style=style_texte,
                             name="HighFrequency")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)
        st_texte.Bind(wx.EVT_SCROLL_CHANGED,
                      self.change_slider,
                      st_texte,
                      SLIDER_F_MAX_TFD)
        self.dico_slider[SLIDER_F_MAX_TFD] = (self.flux_audio.set_f_max, 'dft_modulus')

        page.SetSizerAndFit(ma_grille)
        self.note_book.AddPage(page, name)
        self.ctrl.append(ctrl)
        self.ind_page = self.ind_page + 1

    def ajouter_page_acquisition(self, name="Sampling"):
        """
        création de l'onglet Sampling
        pour paramétrer l'acquisitions
        """
        ctrl = []
        page = wx.Panel(self.note_book)
        font = wx.Font(10,
                       wx.FONTFAMILY_DEFAULT,
                       wx.FONTSTYLE_NORMAL,
                       wx.FONTWEIGHT_BOLD)
        ma_grille = wx.GridSizer(rows=4, cols=2, vgap=5, hgap=5)
        self.dico_label[1000] = ('Start', 'Stop')
        bouton = wx.Button(page, id=START_SAMPLING, label='Start')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.on_start_stop, bouton)
        self.ajouter_bouton((bouton, 0), ctrl, ma_grille, font)

        bouton = wx.Button(page, id=SAVE_SIGNAL, label='Play signal')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.on_play, bouton)
        self.ajouter_bouton((bouton, 0), ctrl, ma_grille, font)

        st_texte = wx.StaticText(page, label="Sampling frequency")

        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)
        choix = []
        for val_freq in self.flux_audio.frequence_dispo:
            choix.append(val_freq)
        self.choix_freq = wx.Choice(page, choices=choix)
        idx = self.choix_freq.FindString(str(float(self.flux_audio.set_frequency())))
        if idx !=  wx.NOT_FOUND:
            self.choix_freq.SetSelection(idx)
        else:
            self.choix_freq.SetSelection(0)
            freq =  self.choix_freq.GetString(0)
            self.flux_audio.set_frequency(float(freq))
            wx.MessageBox("Should not happened. Frequency not found",
                          "Warning",
                          wx.ICON_WARNING)
        self.choix_freq.Bind(wx.EVT_CHOICE, self.maj_interface_freq)
        self.ajouter_bouton((self.choix_freq, 1), ctrl, ma_grille, font)

        # st_texte = wx.TextCtrl(page, value=str(self.flux_audio.Fe))
        # self.ajouter_bouton((st_texte, 1), ctrl, ma_grille, font)

        st_texte = wx.StaticText(page,
                                 label="recording Time (-1 for infinite)")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)

        st_texte = wx.TextCtrl(page, value="-1", id=RECORDING_TIME)
        self.ajouter_bouton((st_texte, 1), ctrl, ma_grille, font)

        st_texte = wx.StaticText(page, label="# sampling before update ")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)

        st_texte = wx.TextCtrl(page,
                               value=str(self.flux_audio.nb_ech_fenetre),
                               id=UPDATE_ECH)
        self.ajouter_bouton((st_texte, 1), ctrl, ma_grille, font)

        page.SetSizerAndFit(ma_grille)
        self.note_book.AddPage(page, name)
        self.ctrl.append(ctrl)
        self.ind_page = self.ind_page + 1

    def maj_choix_freq(self):
        self.choix_freq.Clear()
        choix = []
        for val_freq in self.flux_audio.frequence_dispo:
            self.choix_freq.Append(val_freq)
        idx = self.choix_freq.FindString(str(float(self.flux_audio.set_frequency())))
        if idx !=  wx.NOT_FOUND:
            self.choix_freq.SetSelection(idx)
        else:
            self.choix_freq.SetSelection(0)
            freq =  self.choix_freq.GetString(0)
            self.flux_audio.set_frequency(float(freq))
            wx.MessageBox("Should not happened. Frequency not found",
                          "Warning",
                          wx.ICON_WARNING)


    def maj_interface_freq(self, event):
        idx = self.choix_freq.GetCurrentSelection()
        chaine_freq = self.choix_freq.GetString(idx)
        self.flux_audio.set_frequency(float(chaine_freq))
        self.flux_audio.courbe.maj_limite_slider()
        self.update_spectro_interface()
        self.update_tfd_interface()
        self.flux_audio.courbe.draw_all_axis()

    def ajouter_page_spectrogram(self, name="Spectrogram"):
        """
        création de l'onglet Spectrogram
        pour paramétrer le spectrogramme
        """
        ctrl = []
        page = wx.Panel(self.note_book)
        font = wx.Font(10,
                       wx.FONTFAMILY_DEFAULT,
                       wx.FONTSTYLE_NORMAL,
                       wx.FONTWEIGHT_BOLD)
        ma_grille = wx.GridSizer(rows=9, cols=2, vgap=5, hgap=5)
        self.dico_label[3000] = ('Enable spectrogram',
                                 'Disable spectrogram',
                                 self.ind_page)
        bouton = wx.Button(page, id=3000, label='Enable spectrogram')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.on_enable_graphic, bouton)
        self.ajouter_bouton((bouton, 0), ctrl, ma_grille, font)

        st_texte = wx.StaticText(page, label="")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)

        st_texte = wx.StaticText(page, label="Low frequency (Hz)")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)
        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        st_texte = wx.Slider(page, id=SLIDER_F_MIN_SPECTRO,
                             value=self.flux_audio.f_min_spectro,
                             minValue=0,
                             maxValue=int(self.flux_audio.set_frequency()//2),
                             style=style_texte,
                             name="LowFrequency")
        self.dico_slider[SLIDER_F_MIN_SPECTRO] =\
            (self.flux_audio.set_f_min_spectro, 'spectrogram')
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)
        st_texte.Bind(wx.EVT_SCROLL_CHANGED,
                      self.change_slider,
                      st_texte,
                      SLIDER_F_MIN_SPECTRO)

        st_texte = wx.StaticText(page, label="High frequency (Hz)")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)

        st_texte = wx.Slider(page,
                             id=SLIDER_F_MAX_SPECTRO,
                             value=self.flux_audio.f_max_spectro,
                             minValue=0,
                             maxValue=int(self.flux_audio.set_frequency()//2),
                             style=style_texte,
                             name="HighFrequency")
        self.dico_slider[SLIDER_F_MAX_SPECTRO] =\
            (self.flux_audio.set_f_max_spectro, 'spectrogram')
        self.ajouter_bouton((st_texte, 0),
                            ctrl,
                            ma_grille,
                            font)
        st_texte.Bind(wx.EVT_SCROLL_CHANGED,
                      self.change_slider,
                      st_texte,
                      SLIDER_F_MAX_SPECTRO)

        st_texte = wx.StaticText(page, label="FFT Window size")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)

        st_texte = wx.Slider(page, id=SLIDER_WINDOW_SIZE_SPECTRO,
                             value=self.flux_audio.win_size_spectro,
                             minValue=0,
                             maxValue=self.flux_audio.taille_buffer_signal//16,
                             style=style_texte,
                             name="WindowSize")
        st_texte.Bind(wx.EVT_SCROLL_CHANGED,
                      self.change_slider,
                      st_texte,
                      SLIDER_WINDOW_SIZE_SPECTRO)
        self.dico_slider[SLIDER_WINDOW_SIZE_SPECTRO] = \
            (self.flux_audio.set_win_size_spectro, 'spectrogram')
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)

        st_texte = wx.StaticText(page, label="Overlap")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)

        st_texte = wx.Slider(page,
                             id=SLIDER_OVERLAP_SPECTRO,
                             value=self.flux_audio.overlap_spectro,
                             minValue=0,
                             maxValue=self.flux_audio.nb_ech_fenetre-1,
                             style=style_texte,
                             name="Overlap")
        self.dico_slider[SLIDER_OVERLAP_SPECTRO] =\
            (self.flux_audio.set_overlap_spectro, 'spectrogram')
        st_texte.Bind(wx.EVT_SCROLL_CHANGED,
                      self.change_slider,
                      st_texte,
                      SLIDER_OVERLAP_SPECTRO)
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)

        """
        st_texte = wx.StaticText(page, label="Window")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)
        st_texte = wx.ComboBox(page,
                               id=COMBO_WINDOW_TYPE,
                               choices=self.type_window)
        self.ajouter_bouton((st_texte, 0),
                            ctrl,
                            ma_grille,
                            font,
                            wx.Centre)
        st_texte.SetSelection(self.type_window.index(
            self.flux_audio.type_window)+1)
        st_texte.Bind(wx.EVT_COMBOBOX,
                      self.change_fenetrage,
                      st_texte,
                      COMBO_WINDOW_TYPE)
        st_texte = wx.StaticText(page, id=PARAM1_WINDOW_TYPE-1, label="")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)
        st_texte = wx.TextCtrl(page,
                               id=PARAM1_WINDOW_TYPE,
                               value=str(self.flux_audio.Fe))
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)

        st_texte = wx.StaticText(page, id=PARAM2_WINDOW_TYPE-1, label="")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)
        st_texte = wx.TextCtrl(page,
                               id=PARAM2_WINDOW_TYPE,
                               value=str(self.flux_audio.Fe))
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)
        """
        page.SetSizerAndFit(ma_grille)
        self.note_book.AddPage(page, name)
        self.ctrl.append(ctrl)
        self.ind_page = self.ind_page + 1

    def change_fenetrage(self, event):
        """
        Changement du type de fenêtre pour la tfd
        """
        id_fenetre = event.GetId()
        obj = event.GetEventObject()
        val = obj.GetValue()
        if id_fenetre == COMBO_WINDOW_TYPE:
            self.flux_audio.type_window = val
            self.change_param_window()

    def change_param_window(self):
        """
        Création des articles pour
        régler les paramètres de la fenêtres
        """
        if self.flux_audio.type_window not in self.dico_window:
            return
        param = self.dico_window[self.flux_audio.type_window]
        for idx in range(PARAM1_WINDOW_TYPE-1, PARAM2_WINDOW_TYPE+1):
            fen = wx.Window.FindWindowById(idx)
            fen.Enable(False)
            fen.Show(False)
        if param is None:
            return
        fen = wx.Window.FindWindowById(PARAM1_WINDOW_TYPE-1)
        if fen is not None:
            for idx in range(PARAM1_WINDOW_TYPE-1, PARAM1_WINDOW_TYPE+1):
                fen = wx.Window.FindWindowById(idx)
                fen.Enable(True)
                fen.Show(True)
            fen.SetLabel(param[0])
        if len(param) == 1:
            return
        fen = wx.Window.FindWindowById(PARAM2_WINDOW_TYPE-1)
        if fen is not None:
            for idx in range(PARAM2_WINDOW_TYPE-1, PARAM2_WINDOW_TYPE+1):
                fen = wx.Window.FindWindowById(idx)
                fen.Enable(True)
                fen.Show(True)
            fen.SetLabel(param[1])

    def change_slider(self, event):
        """
        réglage des glissiéres
        """
        obj = event.GetEventObject()
        val = obj.GetValue()
        id_fenetre = event.GetId()
        if id_fenetre not in self.dico_slider:
            return
        self.dico_slider[id_fenetre][0](val)
        if id_fenetre == SLIDER_WINDOW_SIZE_SPECTRO:
            if self.dico_slider[SLIDER_OVERLAP_SPECTRO][0]() > val:
                self.dico_slider[SLIDER_OVERLAP_SPECTRO][0](val-1)
                self.update_spectro_interface()
        self.flux_audio.courbe.draw_all_axis()
        r_upd = self.flux_audio.courbe.GetClientRect()
        self.flux_audio.courbe.Refresh(rect=r_upd)
        # self.flux_audio.courbe.draw_page(None)
        if not self.samp_in_progress:
            self.flux_audio.courbe.maj_page(self.dico_slider[id_fenetre][1])

    def change_tfd_size(self, event):
        """
        réglage de la glissière tfd_size 
        avec mise à jour de la sélection des fréquences
        """
        obj = event.GetEventObject()
        val = obj.GetValue()
        id_fenetre = event.GetId()
        if id_fenetre not in self.dico_slider:
            return
        self.dico_slider[SLIDER_TFD_SIZE][0](val)
        w = wx.Window.FindWindowById(SLIDER_F_MIN_TFD)
        if w is not None:
            self.dico_slider[SLIDER_F_MIN_TFD][0](w.GetValue())
        w = wx.Window.FindWindowById(SLIDER_F_MAX_TFD)
        if w is not None:
            self.dico_slider[SLIDER_F_MAX_TFD][0](w.GetValue())
        if self.flux_audio.courbe.page[1].courbe_active:
            self.flux_audio.courbe.draw_all_axis()
            r_upd = self.flux_audio.courbe.GetClientRect()
            self.flux_audio.courbe.Refresh(rect=r_upd)
            # self.flux_audio.courbe.draw_page(None)
        if not self.samp_in_progress:
            self.flux_audio.courbe.maj_page(self.dico_slider[SLIDER_F_MAX_TFD][1])


    def change_spectro_size(self, event):
        """
        réglage de la glissière tfd_size 
        avec mise à jour de la sélection des fréquences
        OBSOLETE
        """
        obj = event.GetEventObject()
        val = obj.GetValue()
        id_fenetre = event.GetId()
        if id_fenetre not in self.dico_slider:
            return
        w = wx.Window.FindWindowById(SLIDER_F_MIN_SPECTRO)
        if w is not None:
            self.dico_slider[SLIDER_F_MIN_SPECTRO][0](w.GetValue())
        w = wx.Window.FindWindowById(SLIDER_F_MAX_SPECTRO)
        if w is not None:
            self.dico_slider[SLIDER_F_MAX_SPECTRO][0](w.GetValue())
        if self.dico_slider[SLIDER_WINDOW_SIZE_SPECTRO][0]() > self.dico_slider[SLIDER_SPECTRO_SIZE][0](val):
            self.dico_slider[SLIDER_WINDOW_SIZE_SPECTRO][0](self.dico_slider[SLIDER_SPECTRO_SIZE][0]() - 1)
            if self.dico_slider[SLIDER_WINDOW_SIZE_SPECTRO][0]() < self.dico_slider[SLIDER_OVERLAP_SPECTRO][0]():
                self.dico_slider[SLIDER_OVERLAP_SPECTRO][0](self.dico_slider[SLIDER_WINDOW_SIZE_SPECTRO][0]()-1)
        if self.flux_audio.courbe.page[2].courbe_active:
            self.flux_audio.courbe.draw_all_axis()
            r_upd = self.flux_audio.courbe.GetClientRect()
            self.flux_audio.courbe.Refresh(rect=r_upd)
            print("refresh")
        if not self.samp_in_progress:
            self.flux_audio.courbe.maj_page(self.dico_slider[SLIDER_F_MAX_SPECTRO][1])
 

    def update_spectro_interface(self):
        low = wx.Window.FindWindowById(SLIDER_F_MIN_SPECTRO)
        if low:
            low.SetMax(int(self.flux_audio.set_frequency()//2))
        high = wx.Window.FindWindowById(SLIDER_F_MAX_SPECTRO)
        if high:
            high.SetMax(int(self.flux_audio.set_frequency()//2))
        overlap = wx.Window.FindWindowById(SLIDER_OVERLAP_SPECTRO)
        if overlap:
            overlap.SetMax(self.flux_audio.win_size_spectro-1)
        if not self.samp_in_progress:
            self.flux_audio.courbe.maj_page('spectrogram') #self.flux_audio.courbe.draw_page(None)

    def update_tfd_interface(self):
        low = wx.Window.FindWindowById(SLIDER_F_MIN_TFD)
        if low:
            low.SetMax(int(self.flux_audio.set_frequency()//2))
        high = wx.Window.FindWindowById(SLIDER_F_MAX_TFD)
        if high:
            high.SetMax(int(self.flux_audio.set_frequency()//2))
        self.flux_audio.courbe.draw_all_axis()
        if not self.samp_in_progress:
            self.flux_audio.courbe.maj_page("spectrogram")

    def ajouter_bouton(self, bouton, ctrl, ma_grille, font, option=wx.EXPAND):
        bouton[0].SetFont(font)
        ctrl.append(bouton)
        ma_grille.Add(bouton[0], 0, option)

    def set_frequency(self):
        texte_article = self.ctrl[0][3][0].GetValue()
        freq = int(texte_article)
        if freq > 0:
            self.flux_audio.Fe = freq
            return freq
        return None

    def set_window_size(self):
        texte_article = self.ctrl[0][7][0].GetValue()
        nb_ech_fenetre = int(texte_article)
        if nb_ech_fenetre > 0:
            self.flux_audio.nb_ech_fenetre = nb_ech_fenetre
            self.flux_audio.init_data_courbe()
            return nb_ech_fenetre
        return None

    def set_time_length(self):
        """
        Modification de la durée d'acquisition
        en utilisant l'article
        """
        texte_article = self.ctrl[0][5][0].GetValue()
        self.duration = int(texte_article)

    def on_enable_graphic(self, event):
        """
        Gestion de la bascule graphique actif ou inactif
        Modification de la durée d'acquisition
        en utilisant l'article
        """

        bouton = event.GetEventObject()
        id_fenetre = event.GetId()
        if id_fenetre not in self.dico_label:
            return
        couleur = bouton.GetBackgroundColour()
        ind_page = self.dico_label[id_fenetre][2]
        if couleur[1] == 255:
            print("Activation courbe")
            self.update_spectro_interface()
            self.update_tfd_interface()
            bouton.SetBackgroundColour(wx.Colour(255, 0, 0))
            bouton.SetLabel(self.dico_label[id_fenetre][1])
            self.flux_audio.courbe.page[ind_page].courbe_active = True
            self.flux_audio.courbe.draw_all_axis()
            # self.flux_audio.courbe.draw_page(None)

        else:
            print("DesActivation courbe")
            bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
            bouton.SetLabel(self.dico_label[id_fenetre][0])
            self.flux_audio.courbe.page[ind_page].courbe_active = False

    def on_save(self, _):
        """
        Début/Fin de l'acquisition
        """
        with wx.FileDialog(self, "Save file", wildcard="wav files (*.wav)|*.wav",
                               style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:

                if fileDialog.ShowModal() == wx.ID_CANCEL:
                    return
                pathname = fileDialog.GetPath()
                try:
                    self.ind_fichier = self.ind_fichier + 1

                    with soundfile.SoundFile(pathname,
                                             mode='w',
                                             samplerate=self.flux_audio.Fe,
                                             channels=self.flux_audio.nb_canaux,
                                             subtype='FLOAT') as fichier:
                        fichier.write(self.flux_audio.plotdata)
                except IOError:
                    wx.LogError("Cannot save current data in file '%s'." % pathname)        

    def on_play(self, _):
        """
        Ecouter le signal enregistré
        """
        print("try to play on default output")
        sd.play(self.flux_audio.plotdata, self.flux_audio.Fe)


    def on_start_stop(self, event):
        """
        Défut/Fin de l'acquisition
        """
        if self.idmenu_audio_in is None:
            wx.MessageBox("You must select an audio in device",
                          "Warning",
                          wx.ICON_WARNING)
        bouton = event.GetEventObject()
        texte_label = bouton.GetLabel()
        if texte_label == "Start":
            idx = self.choix_freq.GetCurrentSelection()
            chaine_freq = self.choix_freq.GetString(idx)
            self.flux_audio.set_frequency(int(float(chaine_freq)))
            self.set_window_size()
            self.set_time_length()
            self.flux_audio.courbe.draw_all_axis()
            if not self.flux_audio.open(self.idx_periph_in):
                self.disable_item_check()
                wx.MessageBox("Cannot opened input device : input disable",
                              "Error",
                              wx.ICON_WARNING)
                return
            self.update_spectro_interface()
            self.update_tfd_interface()
            self.flux_audio.courbe.page[0].courbe_active = True
            bouton.SetLabel("Stop")
            bouton.SetBackgroundColour(wx.Colour(255, 0, 0))
            self.figer_parametre(True)
            self.samp_in_progress = True
        else:
            self.flux_audio.close()
            self.flux_audio.courbe.page[0].courbe_active = False
            bouton.SetLabel("Start")
            bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
            self.figer_parametre(False)
            self.samp_in_progress = False

    def figer_parametre(self, enable):
        """
        Figer les paramètres non modifiables
        pendant l'acquisiion
        """
        for liste_art in self.ctrl:
            for ctrl in liste_art:
                if ctrl[1]:
                    if enable:
                        ctrl[0].Disable()
                    else:
                        ctrl[0].Enable()


if __name__ == '__main__':
    application = wx.App()
    my_frame = wx.Frame(None, -1, 'Interface')
    my_plotter = InterfaceAnalyseur(my_frame)
    my_frame.Show()
    wx.MessageBox("First choose peripherical in input device menu", "Warning", wx.ICON_WARNING)
    application.MainLoop()
