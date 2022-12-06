"""
Génération de signal echantillonné à la fréquence Fe
d'une durée T 
    chirp
    square
    sinus
    gaussi
"""
# pylint: disable=maybe-no-member
import sys
import soundfile
import sounddevice
import wx
import wx.lib.agw.aui as aui
import numpy as np
import scipy.signal



BOUTON_SAVE_CHIRP = 4001
BOUTON_PLAY_CHIRP = 4002
SLIDER_F0_CHIRP = 4003
SLIDER_F1_CHIRP = 4004
SLIDER_DUREE_CHIRP = 4005

BOUTON_SAVE_SINUS = 5001
BOUTON_PLAY_SINUS = 5002
SLIDER_F0_SINUS = 5003
SLIDER_DUREE_SINUS = 5005
CASE_REFERENCE = 5006

BOUTON_SAVE_SQUARE = 6001
BOUTON_PLAY_SQUARE = 6002
SLIDER_F0_SQUARE = 6003
SLIDER_DUREE_SQUARE = 6005
SLIDER_RAPPORT_CYCLIQUE_SQUARE = 6006

BOUTON_SAVE_GAUSSIAN = 7001
BOUTON_PLAY_GAUSSIAN = 7002
SLIDER_F0_GAUSSIAN = 7003
SLIDER_DUREE_GAUSSIAN = 7005
SLIDER_RAPPORT_CYCLIQUE_GAUSSIAN = 7006




class InterfaceGeneration(wx.Panel):
    """
    onglets pour les réglages de l'acquisition,
    pour les réglages de l'affichage de la tfd,
    pour les réglages de l'affichage du spectrogramme
    """
    def __init__(self, parent, id_fenetre=-1):
        """
        membre :
        parent : fenêtre parent
        note_book : contient les onglets chirp, square, gaussian et sinus
        f0_t0 : fréquence du chirp à t0
        f1_t1 : fréquence du chirp à t1
        Fe : fréquence d'échantillonnage
        duree :  durée du signal
        """
        wx.Panel.__init__(self, parent, id=id_fenetre)
        self.note_book = aui.AuiNotebook(self,
                                         style=aui.AUI_NB_TOP |
                                         aui.AUI_NB_TAB_SPLIT |
                                         aui.AUI_NB_TAB_MOVE |
                                         aui.AUI_NB_MIDDLE_CLICK_CLOSE)

        self.parent = parent
        self.val_Fe = ['11025', '22050', '32000', '44100', '48000', '96000']
        self._f0_t0 = 0
        self._f1_t1 = 440
        self._f0_sinus = 1000
        self._f0_square = 1000
        self._f0_gaussian = 1000
        self._ratio_square = 50
        self._ratio_gaussian = 50
        self.sinus_reference =  True
        self.Fe = 22050
        self.t_ech = None
        self.dico_slider = {0: None}
        self._duree_chirp = 1
        self._duree_sinus = 1
        self._duree_square = 1
        self._duree_gaussian = 1
        self.methode = None
        self.choix_Fe_sinus = None
        self.choix_Fe_chirp =  None
        self.choix_Fe_gaussian =  None
        self.choix_Fe_square =  None
        self.parent.Show()

    def f0_t0(self, f=None):
        if f is not None:
            self._f0_t0 = f
        return self._f0_t0

    def f1_t1(self, f=None):
        if f is not None:
            self._f1_t1 = f
        return self._f1_t1

    def f0_sinus(self, f=None):
        if f is not None:
            self._f0_sinus = f
        return self._f0_sinus

    def f0_gaussian(self, f=None):
        if f is not None:
            self._f0_gaussian = f
        return self._f0_gaussian

    def ratio_square(self, f=None):
        if f is not None:
            self._ratio_square = f
        return self._ratio_square

    def ratio_gaussian(self, f=None):
        if f is not None:
            self._ratio_gaussian = f
        return self._ratio_gaussian

    def f0_square(self, f=None):
        if f is not None:
            self._f0_square = f
        return self._f0_square

    def duree_square(self, f=None):
        if f is not None:
            self._duree_square = f
        return self._duree_square

    def duree_sinus(self, f=None):
        if f is not None:
            self._duree_sinus = f
        return self._duree_sinus

    def duree_chirp(self, f=None):
        if f is not None:
            self._duree_chirp = f
        return self._duree_chirp

    def duree_gaussian(self, f=None):
        if f is not None:
            self._duree_gaussian = f
        return self._duree_gaussian

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


    def ajouter_gadget(self, ctrl, fenetre, ma_grille, font, option=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL):
        ctrl[0].SetFont(font)
        fenetre.append(ctrl)
        ma_grille.Add(ctrl[0], 0, option, 5)


    def interface_generation_fct(self):
        """
        Mise en place de l'interface d'acquisition
        pour le signal temporel, la tfd et le spectrogramme
        """
        sizer = wx.BoxSizer()
        sizer.Add(self.note_book, 1, wx.EXPAND|wx.CENTER)
        self.SetSizer(sizer)
        self.ctrl = []
        self.dico_label = {0: ('Enable', 'Disable', 0)}
        self.dico_slider = {0: None}
        self.ind_page = 0
        self.ajouter_page_sinus()
        self.ajouter_page_chirp()
        self.ajouter_page_square()
        self.ajouter_page_gaussian()
        self.note_book.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.close_page)
        self.note_book.Refresh(True)
        self.note_book.SetSize(self.parent.GetClientSize())


    def install_menu(self):
        """
        Installation des menus
        """
        barre_menu = wx.MenuBar()
        menu_fichier = wx.Menu()
        _ = menu_fichier.Append(wx.ID_EXIT, 'Quit', "exit program")
        barre_menu.Append(menu_fichier, '&File')
        _ = wx.Menu()
        menu_about = wx.Menu()
        _ = menu_about.Append(wx.ID_ABOUT, 'About', 'About Signal wav filee')
        barre_menu.Append(menu_about, '&Help')
        self.parent.SetMenuBar(barre_menu)
        self.parent.Bind(wx.EVT_CLOSE, self.close_page)
        self.parent.Bind(wx.EVT_MENU, self.quitter, id=wx.ID_EXIT)

    def close_page(self, evt):
        """
        surchage de close pour interdire
        la fermeture des onglets
        """
        wx.MessageBox("Cannot be closed", "Warning", wx.ICON_WARNING)
        evt.Veto()

    def quitter(self, _):
        """
        libérer ressource et quitter
        """
        sys.exit()

    def change_slider(self, event):
        """
        réglage des glissiéres
        """
        obj = event.GetEventObject()
        val = obj.GetValue()
        id_fenetre = event.GetId()
        if id_fenetre not in self.dico_slider:
            return
        self.dico_slider[id_fenetre](val)

    def maj_param_chirp(self):
        self.t_ech = np.arange(0,self._duree_chirp,1/self.Fe)
        idx =  self.choix_Fe_chirp.GetCurrentSelection()
        self.Fe = float(self.choix_Fe_chirp.GetString(idx))
        idx =  self.choix_chirp.GetCurrentSelection()
        self.methode = self.choix_chirp.GetString(idx)

    def chirp(self):
        try:
            self.signal = scipy.signal.chirp(self.t_ech, 
                                             self.f0_t0(),
                                             self._duree_chirp,
                                             self.f1_t1(),
                                             method=self.methode)
            return True
        except ValueError as err:
            self.err_msg = str(err)
            return False

    def play_chirp(self, event):
        """
        Jouer le chirp
        """
        self.maj_param_chirp()
        if self.chirp():
            sounddevice.play(self.signal, self.Fe)
        else:
            wx.LogError(self.err_msg)

    def save_chirp(self, event):
        """
        sauvegarde du chirp
        """
        self.maj_param_chirp()
        if self.chirp():
            nom_fichier = "chirp_" + self.methode +  "_"
            nom_fichier = nom_fichier + str(self.duree_chirp()) + "s_"
            nom_fichier = nom_fichier + str(self.f0_t0()) + "_" + str(self.f1_t1())
            nom_fichier = nom_fichier + ".wav"
            with soundfile.SoundFile(nom_fichier,
                                     mode='w',
                                     samplerate=self.Fe,
                                     channels=1,
                                     subtype='FLOAT') as fichier:
                fichier.write(self.signal)
        else:
            wx.LogError(self.err_msg)

    def ajouter_page_chirp(self, name="Chirp"):
        """
        création de l'onglet Chirp
        pour paramétrer le chirp selon doc scipy 
        """
        ctrl = []
        page = wx.Panel(self.note_book)
        font = wx.Font(12,
                       wx.FONTFAMILY_DEFAULT,
                       wx.FONTSTYLE_ITALIC,
                       wx.FONTWEIGHT_BOLD)
        ma_grille = wx.GridSizer(rows=6, cols=2, vgap=20, hgap=20)
        type_chirp = ['linear', 'quadratic', 'logarithmic', 'hyperbolic']
        self.choix_Fe_chirp = wx.Choice(page, choices=self.val_Fe)
        self.choix_Fe_chirp.SetSelection(3)
        self.ajouter_gadget((self.choix_Fe_chirp, 1), ctrl, ma_grille, font)
        st_texte = wx.StaticText(page, label="Sampling frequency (Hz)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)
        self.choix_chirp = wx.Choice(page, choices=type_chirp)
        self.choix_chirp.SetSelection(0)
        self.ajouter_gadget((self.choix_chirp, 1), ctrl, ma_grille, font)
        st_texte = wx.StaticText(page, label="Chirp method")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)

        self.ctrl.append(ctrl)
        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        gadget = wx.Slider(page,
                             id=SLIDER_F0_CHIRP,
                             value=self.f0_t0(),
                             minValue=0,
                             maxValue=self.Fe//2,
                             style=style_texte,
                             name="Frequency t=0")
        self.dico_slider[SLIDER_F0_CHIRP] = self.f0_t0
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_F0_CHIRP)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)
        st_texte = wx.StaticText(page, label="Initial frequency (Hz)")

        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)
        gadget = wx.Slider(page,
                             id=SLIDER_F1_CHIRP,
                             value=self.f1_t1(),
                             minValue=0,
                             maxValue=self.Fe//2,
                             style=style_texte,
                             name="Frequency t=D")
        self.dico_slider[SLIDER_F1_CHIRP] = self.f1_t1
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_F1_CHIRP)
        st_texte = wx.StaticText(page, label="Last frequency (Hz)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)

        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        gadget = wx.Slider(page,
                             id=SLIDER_DUREE_CHIRP,
                             value=self.duree_chirp(),
                             minValue=0,
                             maxValue=2**18 // self.Fe,
                             style=style_texte,
                             name="Duration")
        self.dico_slider[SLIDER_DUREE_CHIRP] = self.duree_chirp
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_DUREE_CHIRP)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        st_texte = wx.StaticText(page, label="Chirp duration (s)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)

        bouton = wx.Button(page, id=BOUTON_SAVE_CHIRP)
        bouton.SetLabel('Save')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.save_chirp, bouton)
        self.ajouter_gadget((bouton, 0), ctrl, ma_grille, font)
        bouton = wx.Button(page, id=BOUTON_PLAY_CHIRP)
        bouton.SetLabel('Play')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.play_chirp, bouton)
        self.ajouter_gadget((bouton, 0), ctrl, ma_grille, font)
        page.SetSizerAndFit(ma_grille)
        self.note_book.AddPage(page, name)
        self.ind_page = self.ind_page + 1


    def maj_param_gaussian(self):
        idx =  self.choix_Fe_gaussian.GetCurrentSelection()
        self.Fe = float(self.choix_Fe_gaussian.GetString(idx))
        self.t_ech = np.arange(-self._duree_gaussian/2,self._duree_gaussian/2,1/self.Fe)

    def signal_gaussian(self):
        self.signal = scipy.signal.gausspulse(self.t_ech, fc=self.f0_gaussian(), bw=self._ratio_gaussian/1000)
        return True

    def save_gaussian(self, event):
        """
        sauvegarde du signal carré
        """
        self.maj_param_gaussian()
        if self.signal_gaussian():
            nom_fichier = "gaussian_" 
            nom_fichier = nom_fichier + str(self.duree_gaussian()) + "s_"
            nom_fichier = nom_fichier + str(self.f0_gaussian()) + "Hz_"
            nom_fichier = nom_fichier + str(self.ratio_gaussian()) 
            nom_fichier = nom_fichier + ".wav"
            with soundfile.SoundFile(nom_fichier,
                                     mode='w',
                                     samplerate=self.Fe,
                                     channels=1,
                                     subtype='FLOAT') as fichier:
                fichier.write(self.signal)
        else:
            wx.LogError(self.err_msg)

    def play_gaussian(self, event):
        """
        Jouer le signal carré
        """
        self.maj_param_gaussian()
        if self.signal_gaussian():
            sounddevice.play(self.signal, self.Fe)
        else:
            wx.LogError(self.err_msg)

    def ajouter_page_gaussian(self, name="gaussian"):
        """
        création de l'onglet un pulse gaussien
        pour paramétrer un gausspulse de fréquence F0 et ratio (BP)
        et de durée 
        """
        ctrl = []
        page = wx.Panel(self.note_book)
        font = wx.Font(12,
                       wx.FONTFAMILY_DEFAULT,
                       wx.FONTSTYLE_ITALIC,
                       wx.FONTWEIGHT_BOLD)
        ma_grille = wx.GridSizer(rows=5, cols=2, vgap=20, hgap=20)
        self.choix_Fe_gaussian = wx.Choice(page, choices=self.val_Fe)
        self.choix_Fe_gaussian.SetSelection(3)
        self.ajouter_gadget((self.choix_Fe_gaussian, 1), ctrl, ma_grille, font)
        st_texte = wx.StaticText(page, label="Sampling frequency (Hz)")

        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)
        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        gadget = wx.Slider(page,
                           id=SLIDER_F0_GAUSSIAN,
                           value=self.f0_gaussian(),
                           minValue=0,
                           maxValue=self.Fe//2,
                           style=style_texte)
        self.dico_slider[SLIDER_F0_GAUSSIAN] = self.f0_gaussian
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_F0_GAUSSIAN)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        st_texte = wx.StaticText(page, label="Frequency  (Hz)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)

        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        gadget = wx.Slider(page,
                           id=SLIDER_DUREE_GAUSSIAN,
                           value=self.duree_gaussian(),
                           minValue=0,
                           maxValue=2**18 // self.Fe,
                           style=style_texte,
                           name="Duration")
        self.dico_slider[SLIDER_DUREE_GAUSSIAN] = self.duree_gaussian
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_DUREE_GAUSSIAN)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        st_texte = wx.StaticText(page, label="Square wave duration (s)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)

        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        gadget = wx.Slider(page,
                           id=SLIDER_RAPPORT_CYCLIQUE_GAUSSIAN,
                           value=self.ratio_square(),
                           minValue=0,
                           maxValue=1000,
                           style=style_texte,
                           name="Duration")
        self.dico_slider[SLIDER_RAPPORT_CYCLIQUE_GAUSSIAN] = self.ratio_gaussian
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_RAPPORT_CYCLIQUE_GAUSSIAN)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        st_texte = wx.StaticText(page, label="Duty cycle (‰)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)


        bouton = wx.Button(page, id=BOUTON_SAVE_GAUSSIAN)
        bouton.SetLabel('Save')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.save_gaussian, bouton)
        self.ajouter_gadget((bouton, 0), ctrl, ma_grille, font)
        bouton = wx.Button(page, id=BOUTON_PLAY_GAUSSIAN)
        bouton.SetLabel('Play')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.play_gaussian, bouton)
        self.ajouter_gadget((bouton, 0), ctrl, ma_grille, font)
        page.SetSizerAndFit(ma_grille)
        self.note_book.AddPage(page, name)
        self.ctrl.append(ctrl)
        self.ind_page = self.ind_page + 1

    def maj_param_sinus(self):
        idx =  self.choix_Fe_sinus.GetCurrentSelection()
        self.Fe = float(self.choix_Fe_sinus.GetString(idx))
        self.t_ech = np.arange(0,self._duree_sinus,1/self.Fe)

    def sinus(self):
        self.signal = np.sin(self.t_ech * 2 * np.pi * self.f0_sinus())
        if self.sinus_reference == True:
            self.signal = self.signal + np.sin(self.t_ech * 2 * np.pi * 1000)
        return True

    def play_sinus(self, event):
        """
        Jouer le sinus
        """
        self.maj_param_sinus()
        if self.sinus():
            sounddevice.play(self.signal, self.Fe)
        else:
            wx.LogError(self.err_msg)

    def save_sinus(self, event):
        """
        sauvegarde du sinus
        """
        self.maj_param_sinus()
        if self.sinus():
            nom_fichier = "sinus_"
            nom_fichier = nom_fichier + str(self.duree_sinus()) + "s_"
            nom_fichier = nom_fichier + str(self.f0_sinus())
            nom_fichier = nom_fichier + ".wav"
            with soundfile.SoundFile(nom_fichier,
                                     mode='w',
                                     samplerate=self.Fe,
                                     channels=1,
                                     subtype='FLOAT') as fichier:
                fichier.write(self.signal)
        else:
            wx.LogError(self.err_msg)

    def maj_sinus_reference(self, evt):
        case = evt.GetEventObject()
        if case.GetValue():
            self.sinus_reference = True
        else:
            self.sinus_reference = False


    def ajouter_page_sinus(self, name="Sinus"):
        """
        création de l'onglet sinus
        pour paramétrer un sinus de fréquence F0 et
        de durée 
        """
        ctrl = []
        page = wx.Panel(self.note_book)
        font = wx.Font(12,
                       wx.FONTFAMILY_DEFAULT,
                       wx.FONTSTYLE_ITALIC,
                       wx.FONTWEIGHT_BOLD)
        ma_grille = wx.GridSizer(rows=5, cols=2, vgap=20, hgap=20)
        self.choix_Fe_sinus = wx.Choice(page, choices=self.val_Fe)
        self.choix_Fe_sinus.SetSelection(3)
        self.ajouter_gadget((self.choix_Fe_sinus, 1), ctrl, ma_grille, font)
        st_texte = wx.StaticText(page, label="Sampling frequency (Hz)")

        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)
        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        gadget = wx.Slider(page,
                           id=SLIDER_F0_SINUS,
                           value=self.f0_sinus(),
                           minValue=0,
                           maxValue=self.Fe//2,
                           style=style_texte)
        self.dico_slider[SLIDER_F0_SINUS] = self.f0_sinus
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_F0_SINUS)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        st_texte = wx.StaticText(page, label="Frequency  (Hz)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)

        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        gadget = wx.Slider(page,
                           id=SLIDER_DUREE_SINUS,
                           value=self.duree_sinus(),
                           minValue=0,
                           maxValue=2**18 // self.Fe,
                           style=style_texte,
                           name="Duration")
        self.dico_slider[SLIDER_DUREE_SINUS] = self.duree_sinus
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_DUREE_SINUS)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        st_texte = wx.StaticText(page, label="Sinusoide duration (s)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)
        case = wx.CheckBox(page, -1, 'Add 1000Hz frequency reference')
        case.SetValue(self.sinus_reference)
        case.Bind(wx.EVT_CHECKBOX,
                    self.maj_sinus_reference,
                    case,
                    CASE_REFERENCE)

        self.ajouter_gadget((case, 0), ctrl, ma_grille, font)
        st_texte = wx.StaticText(page, label="")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font)

        bouton = wx.Button(page, id=BOUTON_SAVE_SINUS)
        bouton.SetLabel('Save')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.save_sinus, bouton)
        self.ajouter_gadget((bouton, 0), ctrl, ma_grille, font)
        bouton = wx.Button(page, id=BOUTON_PLAY_SINUS)
        bouton.SetLabel('Play')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.play_sinus, bouton)
        self.ajouter_gadget((bouton, 0), ctrl, ma_grille, font)
        page.SetSizerAndFit(ma_grille)
        self.note_book.AddPage(page, name)
        self.ctrl.append(ctrl)
        self.ind_page = self.ind_page + 1

    def maj_param_square(self):
        idx =  self.choix_Fe_square.GetCurrentSelection()
        self.Fe = int(float(self.choix_Fe_square.GetString(idx)))
        self.t_ech = np.arange(0,self._duree_square,1/self.Fe)

    def signal_carre(self):
        self.signal = scipy.signal.square(self.t_ech * 2 * np.pi * self.f0_square(), self._ratio_square/100)
        return True

    def save_square(self, event):
        """
        sauvegarde du signal carré
        """
        self.maj_param_square()
        if self.signal_carre():
            nom_fichier = "square_" 
            nom_fichier = nom_fichier + str(self.duree_square()) + "s_"
            nom_fichier = nom_fichier + str(self.f0_square()) + "Hz_"
            nom_fichier = nom_fichier + str(self.ratio_square()) 
            nom_fichier = nom_fichier + ".wav"
            with soundfile.SoundFile(nom_fichier,
                                     mode='w',
                                     samplerate=self.Fe,
                                     channels=1,
                                     subtype='FLOAT') as fichier:
                fichier.write(self.signal)
        else:
            wx.LogError(self.err_msg)

    def play_square(self, event):
        """
        Jouer le signal carré
        """
        self.maj_param_square()
        if self.signal_carre():
            sounddevice.play(self.signal, self.Fe)
        else:
            wx.LogError(self.err_msg)

    def ajouter_page_square(self, name="Square"):
        """
        création de l'onglet sinus
        pour paramétrer un sinus de fréquence F0 et
        de durée 
        """
        ctrl = []
        page = wx.Panel(self.note_book)
        font = wx.Font(12,
                       wx.FONTFAMILY_DEFAULT,
                       wx.FONTSTYLE_ITALIC,
                       wx.FONTWEIGHT_BOLD)
        ma_grille = wx.GridSizer(rows=5, cols=2, vgap=20, hgap=20)
        self.choix_Fe_square = wx.Choice(page, choices=self.val_Fe)
        self.choix_Fe_square.SetSelection(3)
        self.ajouter_gadget((self.choix_Fe_square, 1), ctrl, ma_grille, font)
        st_texte = wx.StaticText(page, label="Sampling frequency (Hz)")

        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)
        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        gadget = wx.Slider(page,
                           id=SLIDER_F0_SQUARE,
                           value=self.f0_square(),
                           minValue=0,
                           maxValue=self.Fe//2,
                           style=style_texte)
        self.dico_slider[SLIDER_F0_SQUARE] = self.f0_square
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_F0_SQUARE)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        st_texte = wx.StaticText(page, label="Frequency  (Hz)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)

        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        gadget = wx.Slider(page,
                           id=SLIDER_DUREE_SQUARE,
                           value=self.duree_square(),
                           minValue=0,
                           maxValue=2**18 // self.Fe,
                           style=style_texte,
                           name="Duration")
        self.dico_slider[SLIDER_DUREE_SQUARE] = self.duree_square
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_DUREE_SQUARE)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        st_texte = wx.StaticText(page, label="Square wave duration (s)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)

        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        gadget = wx.Slider(page,
                           id=SLIDER_RAPPORT_CYCLIQUE_SQUARE,
                           value=self.ratio_square(),
                           minValue=0,
                           maxValue=100,
                           style=style_texte,
                           name="Duration")
        self.dico_slider[SLIDER_RAPPORT_CYCLIQUE_SQUARE] = self.ratio_square
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_RAPPORT_CYCLIQUE_SQUARE)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        st_texte = wx.StaticText(page, label="Duty cycle (%)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)


        bouton = wx.Button(page, id=BOUTON_SAVE_SQUARE)
        bouton.SetLabel('Save')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.save_square, bouton)
        self.ajouter_gadget((bouton, 0), ctrl, ma_grille, font)
        bouton = wx.Button(page, id=BOUTON_PLAY_SQUARE)
        bouton.SetLabel('Play')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.play_square, bouton)
        self.ajouter_gadget((bouton, 0), ctrl, ma_grille, font)
        page.SetSizerAndFit(ma_grille)
        self.note_book.AddPage(page, name)
        self.ctrl.append(ctrl)
        self.ind_page = self.ind_page + 1


    def on_save(self, _):
        """
        Début/Fin de l'acquisition
        """
        self.ind_fichier = self.ind_fichier + 1

        with soundfile.SoundFile("buffer" + str(self.ind_fichier) + ".wav",
                                 mode='w',
                                 samplerate=self.Fe,
                                 channels=1,
                                 subtype='FLOAT') as fichier:
            fichier.write(self.flux_audio.plotdata)



if __name__ == '__main__':
    application = wx.App()
    my_frame = wx.Frame(None, -1, 'Interface')
    my_plotter = InterfaceGeneration(my_frame)
    my_plotter.interface_generation_fct()
    my_frame.Show()
    application.MainLoop()
