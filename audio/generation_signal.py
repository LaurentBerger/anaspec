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
import audio.fluxaudio



BOUTON_SAVE_CHIRP = 14001
BOUTON_PLAY_CHIRP = 14002
SLIDER_F0_CHIRP = 14003
SLIDER_F1_CHIRP = 14004
SLIDER_DUREE_CHIRP = 14005
CASE_REFERENCE_CHIRP = 14006

BOUTON_SAVE_SINUS_CUT = 15201
BOUTON_PLAY_SINUS_CUT = 15202
SLIDER_F0_SINUS_CUT = 15203
SLIDER_DUREE_SINUS_CUT = 15205
SLIDER_CUT_LEVEL = 15206
CASE_REFERENCE_CUT = 15207


BOUTON_SAVE_SINUS = 15301
BOUTON_PLAY_SINUS = 15302
SLIDER_F0_SINUS = 15303
SLIDER_DUREE_SINUS = 15305
CASE_REFERENCE = 15306

BOUTON_SAVE_RAMP = 18001
BOUTON_PLAY_RAMP = 18002
SLIDER_F0_RAMPE_FONCTION = 18003
SLIDER_F0_RAMP = 18004
SLIDER_F1_RAMP = 18005
SLIDER_NB_RAMP = 18006
SLIDER_DUREE_RAMP = 18007
CASE_REFERENCE_RAMP = 18008

BOUTON_SAVE_SQUARE = 16001
BOUTON_PLAY_SQUARE = 16002
SLIDER_F0_SQUARE = 16003
SLIDER_DUREE_SQUARE = 16005
SLIDER_RAPPORT_CYCLIQUE_SQUARE = 16006

BOUTON_SAVE_SAWTOOTH = 16101
BOUTON_PLAY_SAWTOOTH = 16102
SLIDER_F0_SAWTOOTH = 16103
SLIDER_DUREE_SAWTOOTH = 16105
SLIDER_RAPPORT_CYCLIQUE_SAWTOOTH = 16106

BOUTON_SAVE_GAUSSIAN = 17001
BOUTON_PLAY_GAUSSIAN = 17002
SLIDER_F0_GAUSSIAN = 17003
SLIDER_DUREE_GAUSSIAN = 17005
SLIDER_RAPPORT_CYCLIQUE_GAUSSIAN = 17006




class InterfaceGeneration(wx.Panel):
    """
    onglets pour les réglages de l'acquisition,
    pour les réglages de l'affichage de la tfd,
    pour les réglages de l'affichage du spectrogramme
    """
    def __init__(self, parent, fa=None, id_fenetre=-1):
        """
        membre :
        parent : fenêtre parent
        fa: fluxaudio à mettre à jour
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
        self.amplitude = 0.5
        self.fct_ramp = 'sin'
        self._nb_ramp = 10
        self._f0_ramp = 0
        self._f1_ramp = 440
        self._f0_t0 = 0
        self._f1_t1 = 440
        self._f0_sinus = 1000
        self._f0_sinus_cut = 1000
        self._f0_square = 1000
        self._f0_sawtooth = 1000
        self._f0_gaussian = 1000
        self._ratio_square = 50
        self._ratio_sawtooth = 50
        self._ratio_gaussian = 50
        self._sinus_cut_level =  100
        self.chirp_reference =  True
        self.sinus_reference =  True
        self.sinus_reference_cut = True
        self.ramp_reference =  True
        self.Fe = 22050
        self.t_ech = None
        self.dico_slider = {0: None}
        self._duree_ramp = 1000
        self._duree_sawtooth = 1000
        self._duree_chirp = 1000
        self._duree_sinus = 1000
        self._duree_sinus_cut = 1000
        self._duree_square = 1000
        self._duree_gaussian = 1000
        self.methode = None
        self.choix_Fe_sinus = None
        self.choix_Fe_sinus_cut = None
        self.choix_Fe_chirp =  None
        self.choix_Fe_gaussian =  None
        self.choix_Fe_square =  None
        self.choix_Fe_sawtooth =  None
        self.signal = None
        self.flux = fa
        self.parent.Show()

    def f0_t0(self, f=None):
        if f is not None:
            self._f0_t0 = f
        return self._f0_t0

    def f1_t1(self, f=None):
        if f is not None:
            self._f1_t1 = f
        return self._f1_t1

    def nb_ramp(self, f=None):
        if f is not None:
            self._nb_ramp = f
        return self._nb_ramp

    def f0_ramp(self, f=None):
        if f is not None:
            self._f0_ramp = f
        return self._f0_ramp

    def f1_ramp(self, f=None):
        if f is not None:
            self._f1_ramp = f
        return self._f1_ramp

    def f0_sinus(self, f=None):
        if f is not None:
            self._f0_sinus = f
        return self._f0_sinus

    def f0_sinus_cut(self, f=None):
        if f is not None:
            self._f0_sinus_cut = f
        return self._f0_sinus_cut

    def f0_gaussian(self, f=None):
        if f is not None:
            self._f0_gaussian = f
        return self._f0_gaussian

    def ratio_square(self, f=None):
        if f is not None:
            self._ratio_square = f
        return self._ratio_square

    def sinus_cut_level(self, f=None):
        if f is not None:
            self._sinus_cut_level = f
        return self._sinus_cut_level

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

    def ratio_sawtooth(self, f=None):
        if f is not None:
            self._ratio_sawtooth = f
        return self._ratio_sawtooth

    def f0_sawtooth(self, f=None):
        if f is not None:
            self._f0_sawtooth = f
        return self._f0_sawtooth

    def duree_sawtooth(self, f=None):
        if f is not None:
            self._duree_sawtooth = f
        return self._duree_sawtooth

    def duree_sinus(self, f=None):
        if f is not None:
            self._duree_sinus = f
        return self._duree_sinus

    def duree_sinus_cut(self, f=None):
        if f is not None:
            self._duree_sinus_cut = f
        return self._duree_sinus_cut

    def duree_chirp(self, f=None):
        if f is not None:
            self._duree_chirp = f
        return self._duree_chirp

    def duree_ramp(self, f=None):
        if f is not None:
            self._duree_ramp = f
        return self._duree_ramp

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
        self.ajouter_page_sinus_cut()
        self.ajouter_page_chirp()
        self.ajouter_page_square()
        self.ajouter_page_sawtooth()
        self.ajouter_page_gaussian()
        self.ajouter_page_rampe()
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
        idx =  self.choix_Fe_chirp.GetCurrentSelection()
        self.Fe = float(self.choix_Fe_chirp.GetString(idx))
        self.t_ech = np.arange(0,self._duree_chirp/1000,1/self.Fe)
        idx =  self.choix_chirp.GetCurrentSelection()
        self.methode = self.choix_chirp.GetString(idx)

    def chirp(self):
        try:
            self.signal = scipy.signal.chirp(self.t_ech, 
                                             self.f0_t0(),
                                             self._duree_chirp/1000,
                                             self.f1_t1(),
                                             method=self.methode)
            if self.chirp_reference is True:
                self.signal = self.signal + np.sin(self.t_ech * 2 * np.pi * 1000)
            self.signal *= self.amplitude
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
            self.play()
        else:
            wx.LogError(self.err_msg)

    def save_chirp(self, event):
        """
        sauvegarde du chirp
        """
        self.maj_param_chirp()
        if self.chirp():
            nom_fichier = "chirp_" + str(self.Fe) + "_"
            nom_fichier = nom_fichier + self.methode +  "_"
            nom_fichier = nom_fichier + str(self.duree_chirp()) + "ms_"
            nom_fichier = nom_fichier + str(self.f0_t0()) + "_" + str(self.f1_t1())
            nom_fichier = nom_fichier + ".wav"
            self.on_save(nom_fichier)
        else:
            wx.LogError(self.err_msg)

    def maj_chirp_reference(self, evt):
        case = evt.GetEventObject()
        if case.GetValue():
            self.chirp_reference = True
        else:
            self.chirp_reference = False

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
        ma_grille = wx.GridSizer(rows=7, cols=2, vgap=10, hgap=10)
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
                           maxValue=int(self.Fe//2),
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
                             maxValue=int(self.Fe//2),
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
                             maxValue=10000,
                             style=style_texte,
                             name="Duration")
        self.dico_slider[SLIDER_DUREE_CHIRP] = self.duree_chirp
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_DUREE_CHIRP)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        st_texte = wx.StaticText(page, label="Sampling duration (ms)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)
        case = wx.CheckBox(page, -1, 'Add 1000Hz frequency reference')
        case.SetValue(self.chirp_reference)
        case.Bind(wx.EVT_CHECKBOX,
                    self.maj_chirp_reference,
                    case,
                    CASE_REFERENCE_CHIRP)

        self.ajouter_gadget((case, 0), ctrl, ma_grille, font)
        st_texte = wx.StaticText(page, label="")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font)

        bouton = wx.Button(page, id=BOUTON_SAVE_CHIRP)
        bouton.SetLabel('Save')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.save_chirp, bouton)
        self.ajouter_gadget((bouton, 0), ctrl, ma_grille, font)
        bouton = wx.Button(page, id=BOUTON_PLAY_CHIRP)
        if self.flux is not None:
            bouton.SetLabel('Update')
        else:
            bouton.SetLabel('Play')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.play_chirp, bouton)
        self.ajouter_gadget((bouton, 0), ctrl, ma_grille, font)
        page.SetSizerAndFit(ma_grille)
        self.note_book.AddPage(page, name)
        self.maj_param_chirp()
        self.ind_page = self.ind_page + 1


    def maj_param_gaussian(self):
        idx =  self.choix_Fe_gaussian.GetCurrentSelection()
        self.Fe = float(self.choix_Fe_gaussian.GetString(idx))
        self.t_ech = np.arange(-self._duree_gaussian/2000,self._duree_gaussian/2000,1/self.Fe)

    def signal_gaussian(self):
        self.signal = scipy.signal.gausspulse(self.t_ech, fc=self.f0_gaussian(),
                                              bw=(self._ratio_gaussian/1000*self.Fe)/self.f0_gaussian())
        self.signal *= self.amplitude
        return True

    def save_gaussian(self, event):
        """
        sauvegarde du signal carré
        """
        self.maj_param_gaussian()
        if self.signal_gaussian():
            nom_fichier = "gaussian_"+ str(self.Fe) + "_"
            nom_fichier = nom_fichier + str(self.duree_gaussian()) + "ms_"
            nom_fichier = nom_fichier + str(self.f0_gaussian()) + "Hz_"
            nom_fichier = nom_fichier + str(self.ratio_gaussian()) 
            nom_fichier = nom_fichier + ".wav"
            self.on_save(nom_fichier)
        else:
            wx.LogError(self.err_msg)

    def play_gaussian(self, event):
        """
        Jouer le signal carré
        """
        self.maj_param_gaussian()
        if self.signal_gaussian():
            self.play()
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
        ma_grille = wx.GridSizer(rows=5, cols=2, vgap=10, hgap=10)
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
                           maxValue=10000,
                           style=style_texte,
                           name="Duration")
        self.dico_slider[SLIDER_DUREE_GAUSSIAN] = self.duree_gaussian
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_DUREE_GAUSSIAN)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        st_texte = wx.StaticText(page, label="Sampling duration (ms)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)

        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        gadget = wx.Slider(page,
                           id=SLIDER_RAPPORT_CYCLIQUE_GAUSSIAN,
                           value=self.ratio_square(),
                           minValue=0,
                           maxValue=500,
                           style=style_texte,
                           name="Duration")
        self.dico_slider[SLIDER_RAPPORT_CYCLIQUE_GAUSSIAN] = self.ratio_gaussian
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_RAPPORT_CYCLIQUE_GAUSSIAN)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        st_texte = wx.StaticText(page, label="Band width (‰ normalised frequency)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)


        bouton = wx.Button(page, id=BOUTON_SAVE_GAUSSIAN)
        bouton.SetLabel('Save')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.save_gaussian, bouton)
        self.ajouter_gadget((bouton, 0), ctrl, ma_grille, font)
        bouton = wx.Button(page, id=BOUTON_PLAY_GAUSSIAN)
        if self.flux is not None:
            bouton.SetLabel('Update')
        else:
            bouton.SetLabel('Play')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.play_gaussian, bouton)
        self.ajouter_gadget((bouton, 0), ctrl, ma_grille, font)
        page.SetSizerAndFit(ma_grille)
        self.note_book.AddPage(page, name)
        self.ctrl.append(ctrl)
        self.maj_param_gaussian()
        self.ind_page = self.ind_page + 1

    def maj_param_sinus(self):
        idx =  self.choix_Fe_sinus.GetCurrentSelection()
        self.Fe = float(self.choix_Fe_sinus.GetString(idx))
        self.t_ech = np.arange(0,self._duree_sinus/1000,1/self.Fe)

    def sinus(self):
        self.signal = np.sin(self.t_ech * 2 * np.pi * self.f0_sinus())
        if self.sinus_reference == True:
            self.signal = self.signal + np.sin(self.t_ech * 2 * np.pi * 1000)
        self.signal *= self.amplitude
        return True

    def play_sinus(self, event):
        """
        Jouer le sinus
        """
        self.maj_param_sinus()
        if self.sinus():
            self.play()
        else:
            wx.LogError(self.err_msg)

    def save_sinus(self, event):
        """
        sauvegarde du sinus
        """
        self.maj_param_sinus()
        if self.sinus():
            nom_fichier = "sinus_" + str(self.Fe) + "_"
            nom_fichier = nom_fichier + str(self.duree_sinus()) + "ms_"
            nom_fichier = nom_fichier + str(self.f0_sinus())
            nom_fichier = nom_fichier + ".wav"
            self.on_save(nom_fichier)
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
        ma_grille = wx.GridSizer(rows=5, cols=2, vgap=10, hgap=10)
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
                           maxValue=10000,
                           style=style_texte,
                           name="Duration")
        self.dico_slider[SLIDER_DUREE_SINUS] = self.duree_sinus
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_DUREE_SINUS)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        st_texte = wx.StaticText(page, label="Sampling duration (ms)")
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
        if self.flux is not None:
            bouton.SetLabel('Update')
        else:
            bouton.SetLabel('Play')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.play_sinus, bouton)
        self.ajouter_gadget((bouton, 0), ctrl, ma_grille, font)
        page.SetSizerAndFit(ma_grille)
        self.note_book.AddPage(page, name)
        self.ctrl.append(ctrl)
        self.maj_param_sinus()
        self.ind_page = self.ind_page + 1

    def maj_param_sinus_cut(self):
        idx =  self.choix_Fe_sinus_cut.GetCurrentSelection()
        self.Fe = float(self.choix_Fe_sinus_cut.GetString(idx))
        self.t_ech = np.arange(0,self._duree_sinus_cut/1000,1/self.Fe)

    def sinus_cut(self):
        self.signal = np.sin(self.t_ech * 2 * np.pi * self.f0_sinus_cut())
        idx = self.signal > self.sinus_cut_level()/100
        self.signal[idx] = self.sinus_cut_level()/100
        idx = self.signal < -self.sinus_cut_level()/100
        self.signal[idx] = -self.sinus_cut_level()/100
        self.signal = self.signal / self.sinus_cut_level() * 100
        if self.sinus_reference_cut == True:
            self.signal = self.signal + np.sin(self.t_ech * 2 * np.pi * 1000)
        self.signal *= self.amplitude
        return True

    def play_sinus_cut(self, event):
        """
        Jouer le sinus
        """
        self.maj_param_sinus_cut()
        if self.sinus_cut():
            self.play()
        else:
            wx.LogError(self.err_msg)

    def save_sinus_cut(self, event):
        """
        sauvegarde du sinus
        """
        self.maj_param_sinu_cut()
        if self.sinus_cut():
            nom_fichier = "sinus_cut" + str(self.Fe) + "_"
            nom_fichier = nom_fichier + str(self.duree_sinus_cut()) + "ms_"
            nom_fichier = nom_fichier + str(self.f0_sinus_cut())
            nom_fichier = nom_fichier + ".wav"
            self.on_save(nom_fichier)
        else:
            wx.LogError(self.err_msg)

    def maj_sinus_reference_cut(self, evt):
        case = evt.GetEventObject()
        if case.GetValue():
            self.sinus_reference_cut = True
        else:
            self.sinus_reference_cut = False


    def ajouter_page_sinus_cut(self, name="Truncated Sinus "):
        """
        création de l'onglet sinus tronqué
        pour paramétrer un sinus de fréquence F0 et
        de durée 
        """
        ctrl = []
        page = wx.Panel(self.note_book)
        font = wx.Font(12,
                       wx.FONTFAMILY_DEFAULT,
                       wx.FONTSTYLE_ITALIC,
                       wx.FONTWEIGHT_BOLD)
        ma_grille = wx.GridSizer(rows=6, cols=2, vgap=10, hgap=10)
        self.choix_Fe_sinus_cut = wx.Choice(page, choices=self.val_Fe)
        self.choix_Fe_sinus_cut.SetSelection(3)
        self.ajouter_gadget((self.choix_Fe_sinus_cut, 1), ctrl, ma_grille, font)
        st_texte = wx.StaticText(page, label="Sampling frequency (Hz)")

        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)
        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        gadget = wx.Slider(page,
                           id=SLIDER_F0_SINUS_CUT,
                           value=self.f0_sinus_cut(),
                           minValue=0,
                           maxValue=int(self.Fe//2),
                           style=style_texte)
        self.dico_slider[SLIDER_F0_SINUS_CUT] = self.f0_sinus_cut
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_F0_SINUS_CUT)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        st_texte = wx.StaticText(page, label="Frequency  (Hz)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)

        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        gadget = wx.Slider(page,
                           id=SLIDER_DUREE_SINUS_CUT,
                           value=self.duree_sinus_cut(),
                           minValue=0,
                           maxValue=10000,
                           style=style_texte,
                           name="Duration")
        self.dico_slider[SLIDER_DUREE_SINUS_CUT] = self.duree_sinus_cut
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_DUREE_SINUS_CUT)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        st_texte = wx.StaticText(page, label="Sampling duration (ms)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)
        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        gadget = wx.Slider(page,
                           id=SLIDER_CUT_LEVEL,
                           value=self.sinus_cut_level(),
                           minValue=0,
                           maxValue=100,
                           style=style_texte,
                           name="Level")
        self.dico_slider[SLIDER_CUT_LEVEL] = self.sinus_cut_level
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_CUT_LEVEL)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        st_texte = wx.StaticText(page, label="Level (%)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)
        case = wx.CheckBox(page, -1, 'Add 1000Hz frequency reference')
        case.SetValue(self.sinus_reference)
        case.Bind(wx.EVT_CHECKBOX,
                    self.maj_sinus_reference_cut,
                    case,
                    CASE_REFERENCE_CUT)

        self.ajouter_gadget((case, 0), ctrl, ma_grille, font)
        st_texte = wx.StaticText(page, label="")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font)

        bouton = wx.Button(page, id=BOUTON_SAVE_SINUS_CUT)
        bouton.SetLabel('Save')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.save_sinus_cut, bouton)
        self.ajouter_gadget((bouton, 0), ctrl, ma_grille, font)
        bouton = wx.Button(page, id=BOUTON_PLAY_SINUS_CUT)
        if self.flux is not None:
            bouton.SetLabel('Update')
        else:
            bouton.SetLabel('Play')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.play_sinus_cut, bouton)
        self.ajouter_gadget((bouton, 0), ctrl, ma_grille, font)

        page.SetSizerAndFit(ma_grille)
        self.note_book.AddPage(page, name)
        self.ctrl.append(ctrl)
        self.maj_param_sinus_cut()
        self.ind_page = self.ind_page + 1

    def maj_param_square(self):
        idx =  self.choix_Fe_square.GetCurrentSelection()
        self.Fe = int(float(self.choix_Fe_square.GetString(idx)))
        self.t_ech = np.arange(0,self._duree_square/1000,1/self.Fe)

    def signal_carre(self):
        self.signal = scipy.signal.square(self.t_ech * 2 * np.pi * self.f0_square(), self._ratio_square/100)
        self.signal *= self.amplitude
        return True

    def save_square(self, event):
        """
        sauvegarde du signal carré
        """
        self.maj_param_square()
        if self.signal_carre():
            nom_fichier = "square_" + str(self.Fe) + "_"
            nom_fichier = nom_fichier + str(self.duree_square()) + "ms_"
            nom_fichier = nom_fichier + str(self.f0_square()) + "Hz_"
            nom_fichier = nom_fichier + str(self.ratio_square()) 
            nom_fichier = nom_fichier + ".wav"
            self.on_save(nom_fichier)
        else:
            wx.LogError(self.err_msg)

    def play(self):
        if self.flux is None:
            sounddevice.play(self.signal, self.Fe)
        else:
            if str(float(self.Fe)) in self.flux.frequence_dispo:
                if self.Fe != self.flux.Fe:
                    self.flux.set_frequency(self.Fe)
                    wx.MessageBox("Update Sampling frequency to "+ str(self.flux.Fe) + "Hz", "Warning", wx.ICON_WARNING)
                self.flux.update_signal_genere(self.signal)
            else:
                wx.MessageBox("Sampling frequency are not equal\n "+ str(self.flux.Fe) + "Hz<> " +str(self.Fe), "Error", wx.ICON_ERROR)

    def play_square(self, event):
        """
        Jouer le signal carré
        """
        self.maj_param_square()
        if self.signal_carre():
            self.play()
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
        ma_grille = wx.GridSizer(rows=5, cols=2, vgap=10, hgap=10)
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
                           maxValue=int(self.Fe//2),
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
                           maxValue=10000,
                           style=style_texte,
                           name="Duration")
        self.dico_slider[SLIDER_DUREE_SQUARE] = self.duree_square
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_DUREE_SQUARE)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        st_texte = wx.StaticText(page, label="Sampling duration (ms)")
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
        if self.flux is not None:
            bouton.SetLabel('Update')
        else:
            bouton.SetLabel('Play')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.play_square, bouton)
        self.ajouter_gadget((bouton, 0), ctrl, ma_grille, font)
        page.SetSizerAndFit(ma_grille)
        self.note_book.AddPage(page, name)
        self.ctrl.append(ctrl)
        self.maj_param_square()
        self.ind_page = self.ind_page + 1

    def maj_param_sawtooth(self):
        idx =  self.choix_Fe_sawtooth.GetCurrentSelection()
        self.Fe = int(float(self.choix_Fe_sawtooth.GetString(idx)))
        self.t_ech = np.arange(0,self._duree_sawtooth/1000,1/self.Fe)

    def signal_sawtooth(self):
        self.signal = scipy.signal.sawtooth(self.t_ech * 2 * np.pi * self.f0_sawtooth(), self._ratio_sawtooth/100)
        self.signal *= self.amplitude
        return True

    def save_sawtooth(self, event):
        """
        sauvegarde du signal carré
        """
        self.maj_param_square()
        if self.signal_carre():
            nom_fichier = "sawtooth_" + str(self.Fe) + "_"
            nom_fichier = nom_fichier + str(self.duree_sawtooth()) + "ms_"
            nom_fichier = nom_fichier + str(self.f0_sawtooth()) + "Hz_"
            nom_fichier = nom_fichier + str(self.ratio_sawtooth()) 
            nom_fichier = nom_fichier + ".wav"
            self.on_save(nom_fichier)
        else:
            wx.LogError(self.err_msg)

    def play_sawtooth(self, event):
        """
        Jouer le signal carré
        """
        self.maj_param_sawtooth()
        if self.signal_sawtooth():
            self.play()
        else:
            wx.LogError(self.err_msg)

    def ajouter_page_sawtooth(self, name="Sawtooth"):
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
        ma_grille = wx.GridSizer(rows=5, cols=2, vgap=10, hgap=10)
        self.choix_Fe_sawtooth = wx.Choice(page, choices=self.val_Fe)
        self.choix_Fe_sawtooth.SetSelection(3)
        self.ajouter_gadget((self.choix_Fe_sawtooth, 1), ctrl, ma_grille, font)
        st_texte = wx.StaticText(page, label="Sampling frequency (Hz)")

        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)
        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        gadget = wx.Slider(page,
                           id=SLIDER_F0_SAWTOOTH,
                           value=self.f0_sawtooth(),
                           minValue=0,
                           maxValue=int(self.Fe//2),
                           style=style_texte)
        self.dico_slider[SLIDER_F0_SAWTOOTH] = self.f0_sawtooth
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_F0_SAWTOOTH)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        st_texte = wx.StaticText(page, label="Frequency  (Hz)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)

        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        gadget = wx.Slider(page,
                           id=SLIDER_DUREE_SAWTOOTH,
                           value=self.duree_sawtooth(),
                           minValue=0,
                           maxValue=10000,
                           style=style_texte,
                           name="Duration")
        self.dico_slider[SLIDER_DUREE_SAWTOOTH] = self.duree_sawtooth
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_DUREE_SAWTOOTH)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        st_texte = wx.StaticText(page, label="Sampling duration (ms)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)

        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        gadget = wx.Slider(page,
                           id=SLIDER_RAPPORT_CYCLIQUE_SAWTOOTH,
                           value=self.ratio_sawtooth(),
                           minValue=0,
                           maxValue=100,
                           style=style_texte,
                           name="Duration")
        self.dico_slider[SLIDER_RAPPORT_CYCLIQUE_SAWTOOTH] = self.ratio_sawtooth
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_RAPPORT_CYCLIQUE_SAWTOOTH)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        st_texte = wx.StaticText(page, label="Duty cycle (%)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)


        bouton = wx.Button(page, id=BOUTON_SAVE_SAWTOOTH)
        bouton.SetLabel('Save')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.save_sawtooth, bouton)
        self.ajouter_gadget((bouton, 0), ctrl, ma_grille, font)
        bouton = wx.Button(page, id=BOUTON_PLAY_SQUARE)
        if self.flux is not None:
            bouton.SetLabel('Update')
        else:
            bouton.SetLabel('Play')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.play_sawtooth, bouton)
        self.ajouter_gadget((bouton, 0), ctrl, ma_grille, font)
        page.SetSizerAndFit(ma_grille)
        self.note_book.AddPage(page, name)
        self.ctrl.append(ctrl)
        self.maj_param_sawtooth()
        self.ind_page = self.ind_page + 1


    def on_save(self, nom_fichier):
        """
        Début/Fin de l'acquisition
        """
        with soundfile.SoundFile(nom_fichier,
                                    mode='w',
                                    samplerate=int(self.Fe),
                                    channels=1,
                                    subtype='FLOAT') as fichier:
            fichier.write(self.signal)
        wx.MessageBox("save as "+ nom_fichier, "Warning", wx.ICON_WARNING)


    def maj_param_ramp(self):
        idx =  self.choix_Fe_ramp.GetCurrentSelection()
        self.Fe = float(self.choix_Fe_ramp.GetString(idx))
        self.t_ech = np.arange(0,self._duree_ramp/1000,1/self.Fe)
        if self.signal is None or self.signal.shape[0] != self.t_ech.shape[0]:
            self.signal = np.zeros(shape=self.t_ech.shape[0], dtype=np.float64)
        idx =  self.choix_ramp.GetCurrentSelection()
        self.fct_ramp = self.choix_ramp.GetString(idx)

    def ramp(self):
        try:
            t_beg = 0
            t_end = self.t_ech.shape[0] // self._nb_ramp
            width = t_end
            f = self._f0_ramp
            t = self.t_ech[0: width]
            if self.fct_ramp == 'gausspulse':
                t = t - t[-1]/2
            df = (self._f1_ramp - self._f0_ramp) / self._nb_ramp
            # self.t_ech = np.arange(-self._duree_gaussian/2000,self._duree_gaussian/2000,1/self.Fe)
            for idx in range(self._nb_ramp):
                match self.fct_ramp:
                    case 'sin':
                        self.signal[t_beg: t_end] = np.sin(np.pi * 2 * t * f)
                    case 'square':
                        self.signal[t_beg: t_end] = scipy.signal.square(t * 2 * np.pi * f, self._ratio_square/100)
                    case 'gausspulse':
                        self.signal[t_beg: t_end] = scipy.signal.gausspulse(t, fc=f, bw=self._ratio_gaussian/1000)
                    case 'chirp':
                        self.signal[t_beg: t_end] = scipy.signal.chirp(t, f + df * 0.9, t[-1], f, method=self.methode)
                    case _:
                        raise ValueError("Unknown ramp function ")
                self.signal[t_beg: t_end] *= self.amplitude
                t_beg = t_end
                t_end = t_end + width
                f = (idx + 1) * df + self._f0_ramp
            if self.ramp_reference is True:
                self.signal[:] += np.sin(2 * np.pi * 1000 *self.t_ech) * self.amplitude / self._nb_ramp
            if self.flux is not None:
                self.flux.update_signal_genere(self.signal)
            return True
        except ValueError as err:
            self.err_msg = str(err)
            return False

    def play_ramp(self, event):
        """
        Jouer la rampe
        """
        self.maj_param_ramp()
        if self.ramp():
            if self.flux is None:
                sounddevice.play(self.signal, self.Fe)
        else:
            wx.LogError(self.err_msg)

    def save_ramp(self, event):
        """
        sauvegarde du chirp
        """
        self.maj_param_ramp()
        if self.ramp():
            nom_fichier = "ramp" + str(self.Fe) + "_"
            nom_fichier = nom_fichier + "ramp_" + self.fct_ramp +  "_"
            nom_fichier = nom_fichier + str(self.duree_ramp()) + "ms_"
            nom_fichier = nom_fichier + str(self.f0_ramp()) + "_" + str(self.f1_ramp())
            nom_fichier = nom_fichier + "_" + str(self.nb_ramp())
            nom_fichier = nom_fichier + ".wav"
            self.on_save(nom_fichier)
        else:
            wx.LogError(self.err_msg)

    def maj_ramp_reference(self, evt):
        case = evt.GetEventObject()
        if case.GetValue():
            self.ramp_reference = True
        else:
            self.ramp_reference = False

    def ajouter_page_rampe(self, name="Ramp"):
        """
        création de l'onglet Rampe
        pour paramétrer les signaux de type rampe chirp 
        """
        ctrl = []
        page = wx.Panel(self.note_book)
        font = wx.Font(12,
                       wx.FONTFAMILY_DEFAULT,
                       wx.FONTSTYLE_ITALIC,
                       wx.FONTWEIGHT_BOLD)
        ma_grille = wx.GridSizer(rows=8, cols=2, vgap=10, hgap=10)
        type_fct = ['sin', 'square', 'gausspulse', 'chirp']
        self.choix_Fe_ramp = wx.Choice(page, choices=self.val_Fe)
        self.choix_Fe_ramp.SetSelection(3)
        self.ajouter_gadget((self.choix_Fe_ramp, 1), ctrl, ma_grille, font)
        st_texte = wx.StaticText(page, label="Sampling frequency (Hz)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)
        self.choix_ramp = wx.Choice(page, choices=type_fct)
        self.choix_ramp.SetSelection(0)
        self.ajouter_gadget((self.choix_ramp, 1), ctrl, ma_grille, font)
        st_texte = wx.StaticText(page, label="Function")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)

        self.ctrl.append(ctrl)
        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        gadget = wx.Slider(page,
                           id=SLIDER_F0_RAMP,
                           value=self.f0_ramp(),
                           minValue=0,
                           maxValue=int(self.Fe//2),
                           style=style_texte,
                           name="Frequency t=0")
        self.dico_slider[SLIDER_F0_RAMP] = self.f0_ramp
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_F0_RAMP)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)
        st_texte = wx.StaticText(page, label="Initial frequency (Hz)")

        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)
        gadget = wx.Slider(page,
                           id=SLIDER_F1_RAMP,
                           value=self.f1_ramp(),
                           minValue=0,
                           maxValue=int(self.Fe//2),
                           style=style_texte,
                           name="Frequency t=D")
        self.dico_slider[SLIDER_F1_RAMP] = self.f1_ramp
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_F1_RAMP)
        st_texte = wx.StaticText(page, label="Last frequency (Hz)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)

        gadget = wx.Slider(page,
                           id=SLIDER_NB_RAMP,
                           value=self.nb_ramp(),
                           minValue=1,
                           maxValue=100,
                           style=style_texte,
                           name="Frequency t=D")
        self.dico_slider[SLIDER_NB_RAMP] = self.nb_ramp
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_NB_RAMP)
        st_texte = wx.StaticText(page, label="# step")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)

        
        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        gadget = wx.Slider(page,
                             id=SLIDER_DUREE_RAMP,
                             value=self.duree_ramp(),
                             minValue=0,
                             maxValue=10000,
                             style=style_texte,
                             name="Duration")
        self.dico_slider[SLIDER_DUREE_RAMP] = self.duree_ramp
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_DUREE_RAMP)
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        st_texte = wx.StaticText(page, label="Sampling duration (ms)")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)
        case = wx.CheckBox(page, -1, 'Add 1000Hz frequency reference')
        case.SetValue(self.ramp_reference)
        case.Bind(wx.EVT_CHECKBOX,
                    self.maj_ramp_reference,
                    case,
                    CASE_REFERENCE_RAMP)
        self.ajouter_gadget((case, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP|wx.LEFT)
        st_texte = wx.StaticText(page, label="")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font, wx.EXPAND|wx.TOP)

        bouton = wx.Button(page, id=BOUTON_SAVE_RAMP)
        bouton.SetLabel('Save')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.save_ramp, bouton)
        self.ajouter_gadget((bouton, 0), ctrl, ma_grille, font)
        bouton = wx.Button(page, id=BOUTON_PLAY_RAMP)
        if self.flux is not None:
            bouton.SetLabel('Update')
        else:
            bouton.SetLabel('Play')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.play_ramp, bouton)
        self.ajouter_gadget((bouton, 0), ctrl, ma_grille, font)
        page.SetSizerAndFit(ma_grille)
        self.note_book.AddPage(page, name)
        self.maj_param_ramp()
        self.ind_page = self.ind_page + 1



if __name__ == '__main__':
    application = wx.App()
    my_frame = wx.Frame(None, -1, 'Interface', size=(770,360))
    my_plotter = InterfaceGeneration(my_frame)
    my_plotter.interface_generation_fct()
    my_frame.Show()
    application.MainLoop()
