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

BOUTON_SAVE_SINUS = 5001
BOUTON_PLAY_SINUS = 5002
SLIDER_F0_SINUS = 5003

BOUTON_SAVE_SQUARE = 6001
BOUTON_PLAY_SQUARE = 6002
SLIDER_F0_SQUARE = 6003




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
        self._f0_t0 = 0
        self._f1_t1 = 1000
        self._f0_sinus = 1000
        self._f0_square = 1000
        self.Fe = 22050
        self.t_ech = None
        self.dico_slider = {0: None}
        self.duree = 1
        self.methode = None
        self.choix_Fe_sinus = None
        self.choix_Fe_chirp =  None
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

    def f0_square(self, f=None):
        if f is not None:
            self._f0_square = f
        return self._f0_square

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
        ma_grille.Add(ctrl[0], 0, option)


    def interface_acquisition(self):
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
        self.t_ech = np.arange(0,self.duree,1/self.Fe)
        idx =  self.choix_chirp.GetCurrentSelection()
        self.methode = self.choix_chirp.GetString(idx)

    def chirp(self):
        try:
            self.signal = scipy.signal.chirp(self.t_ech, 
                                             self.f0_t0(),
                                             self.duree,
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
            nom_fichier = nom_fichier + str(self.duree) + "s_"
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
        ma_grille = wx.GridSizer(rows=5, cols=2, vgap=20, hgap=20)
        type_chirp = ['linear', 'quadratic', 'logarithmic', 'hyperbolic']
        st_texte = wx.StaticText(page, label="Sampling frequency")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font)
        val_Fe = ['11025', '22050', '32000', '44100', '48000', '96000']
        self.choix_Fe_chirp = wx.Choice(page, choices=val_Fe)
        self.choix_Fe_chirp.SetSelection(3)
        self.ajouter_gadget((self.choix_Fe_chirp, 1), ctrl, ma_grille, font)
        st_texte = wx.StaticText(page, label="Chirp method")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font)
        self.choix_chirp = wx.Choice(page, choices=type_chirp)
        self.choix_chirp.SetSelection(0)
        self.ajouter_gadget((self.choix_chirp, 1), ctrl, ma_grille, font)

        page.SetSizerAndFit(ma_grille)
        self.note_book.AddPage(page, name)
        self.ctrl.append(ctrl)
        st_texte = wx.StaticText(page, label="Initial frequency")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font)
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

        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font)
        st_texte = wx.StaticText(page, label="Last frequency")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font)
        gadget = wx.Slider(page,
                             id=SLIDER_F1_CHIRP,
                             value=self.f1_t1(),
                             minValue=0,
                             maxValue=self.Fe//2,
                             style=style_texte,
                             name="Frequency t=D")
        self.dico_slider[SLIDER_F1_CHIRP] = self.f1_t1
        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font)
        gadget.Bind(wx.EVT_SCROLL,
                    self.change_slider,
                    gadget,
                    SLIDER_F1_CHIRP)
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
        self.ind_page = self.ind_page + 1


    def ajouter_page_gaussian(self, name="Gaussian"):
        """
        création de l'onglet Chirp
        pour paramétrer le chirp selon doc scipy 
        """
        ctrl = []
        page = wx.Panel(self.note_book)
        font = wx.Font(10,
                       wx.FONTFAMILY_DEFAULT,
                       wx.FONTSTYLE_NORMAL,
                       wx.FONTWEIGHT_BOLD)
        ma_grille = wx.GridSizer(rows=3, cols=2, vgap=5, hgap=5)

        page.SetSizerAndFit(ma_grille)
        self.note_book.AddPage(page, name)
        self.ctrl.append(ctrl)
        self.ind_page = self.ind_page + 1

    def maj_param_sinus(self):
        self.t_ech = np.arange(0,self.duree,1/self.Fe)
        idx =  self.choix_chirp.GetCurrentSelection()
        self.methode = self.choix_chirp.GetString(idx)

    def sinus(self):
        self.signal = np.sin(self.t_ech * 2 * np.pi * self.f0_sinus())
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
            nom_fichier = "sinus_" + self.methode +  "_"
            nom_fichier = nom_fichier + str(self.duree) + "s_"
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
        st_texte = wx.StaticText(page, label="Sampling frequency")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font)
        val_Fe = ['11025', '22050', '32000', '44100', '48000', '96000']
        self.choix_Fe_sinus = wx.Choice(page, choices=val_Fe)
        self.choix_Fe_sinus.SetSelection(3)
        self.ajouter_gadget((self.choix_Fe_sinus, 1), ctrl, ma_grille, font)
        st_texte = wx.StaticText(page, label="Frequency")
        self.ajouter_gadget((st_texte, 0), ctrl, ma_grille, font)
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

        self.ajouter_gadget((gadget, 0), ctrl, ma_grille, font)
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


    def ajouter_page_square(self, name="Square"):
        """
        création de l'onglet Chirp
        pour paramétrer le chirp selon doc scipy 
        """
        ctrl = []
        page = wx.Panel(self.note_book)
        font = wx.Font(10,
                       wx.FONTFAMILY_DEFAULT,
                       wx.FONTSTYLE_NORMAL,
                       wx.FONTWEIGHT_BOLD)
        ma_grille = wx.GridSizer(rows=3, cols=2, vgap=5, hgap=5)

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
    my_plotter.interface_acquisition()
    my_frame.Show()
    application.MainLoop()
