"""
Interface de l'analyseur :
réglages des paramètres d'acquisition
pour la tfd, sélection de la bande de fréquence pour l'affichage
pour le spectrogramme, sélection de la bande de fréquence, du nombre
d'échantillon, du recouvrement, du type de fenêtrage
"""
# pylint: disable=maybe-no-member
import os
from pickle import NONE
import sys
import ctypes.wintypes
import numpy as np
import soundfile
import sounddevice as sd
import wx
import wx.adv
import wx.aui as aui
import audio.fluxaudio as fluxaudio
import audio.fenetrecourbe as fc
import audio.generation_signal as generation_signal
import audio.grid_frequency
import audio.mp3_wav
import wx.lib.agw.pyprogress


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

SLIDER_BP_VALUE = 4001
SLIDER_PEAK_DISTANCE = 4002

ID_OPEN_REF = 1101
ID_SIGGEN = 1102
ID_ZEROPADDING = 1103
ID_ZEROPADDING_CENTER = 1104
ID_WAVMP3WAV = 1105
ID_LOG = 1106
ID_MARKER_VALUES = ID_LOG +1
CHOICE_PALETTE = 3007



PARAM1_WINDOW_TYPE = COMBO_WINDOW_TYPE + 2
PARAM2_WINDOW_TYPE = PARAM1_WINDOW_TYPE + 2
PARAM3_WINDOW_TYPE = PARAM2_WINDOW_TYPE + 2


# https://matplotlib.org/stable/tutorials/colors/colormaps.html#lightness-of-matplotlib-colormaps
PALETTE_NAME = ['viridis', 'plasma', 'inferno', 'magma', 'cividis',
                'Pastel1', 'Pastel2', 'Paired', 'Accent', 'Dark2',
                'Set1', 'Set2', 'Set3', 'tab10', 'tab20', 'tab20b',
                'tab20c',
                'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
                'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu',
                'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn',
                'binary', 'gist_yarg', 'gist_gray', 'gray', 'bone',
                'pink', 'spring', 'summer', 'autumn', 'winter', 'cool',
                'Wistia', 'hot', 'afmhot', 'gist_heat', 'copper',
                'PiYG', 'PRGn', 'BrBG', 'PuOr', 'RdGy', 'RdBu', 'RdYlBu',
                'RdYlGn', 'Spectral', 'coolwarm', 'bwr', 'seismic',
                'twilight', 'twilight_shifted', 'hsv',
                'flag', 'prism', 'ocean', 'gist_earth', 'terrain',
                'gist_stern', 'gnuplot', 'gnuplot2', 'CMRmap',
                'cubehelix', 'brg', 'gist_rainbow', 'rainbow', 'jet',
                'turbo', 'nipy_spectral', 'gist_ncar'
                ]


# https://stackoverflow.com/questions/59778250/how-to-disable-quickedit-mode-with-python
def disable_quick_edit_mode():
    kernel32 = ctypes.WinDLL('kernel32')
    dword_for_std_input_handle = ctypes.wintypes.DWORD(-10) # https://learn.microsoft.com/en-us/windows/console/getstdhandle
    dword_for_enable_extended_flags = ctypes.wintypes.DWORD(0x0080) # https://learn.microsoft.com/en-us/windows/console/setconsolemode
    std_input_handle = kernel32.GetStdHandle(dword_for_std_input_handle)
    kernel32.SetConsoleMode(std_input_handle, dword_for_enable_extended_flags)
    last_error = kernel32.GetLastError()
    return last_error

class LogOscillo(wx.LogWindow):
    def __init__(self,pParent, szTitle, show=True, passToOld=True):
        wx.LogWindow.__init__(self, pParent,  szTitle, show, passToOld)
        self.GetFrame().Move(0,280)
    
    def OnFrameClose(self, frame):
        self.Show(False)
        return False


#---------------------------------------------------------------------------

class MySplashScreen(wx.adv.SplashScreen):
    """
    Create a splash screen widget.
    https://wiki.wxpython.org/How%20to%20create%20a%20splash%20screen%20%28Phoenix%29
    """
    def __init__(self, parent=None):

        #------------

        # This is a recipe to a the screen.
        # Modify the following variables as necessary.
        dir_path = os.path.dirname(os.path.realpath(__file__))
        bitmap = wx.Bitmap(name=dir_path+"/anaspec.jpg", type=wx.BITMAP_TYPE_JPEG)
        splash = wx.adv.SPLASH_TIMEOUT
        duration = 3000 # milliseconds

        # Call the constructor with the above arguments
        # in exactly the following order.
        super(MySplashScreen, self).__init__(bitmap=bitmap,
                                             splashStyle=splash,
                                             milliseconds=duration,
                                             parent=None,
                                             id=-1,
                                             pos=(0, 0),
                                             size=wx.DefaultSize,
                                             style=wx.STAY_ON_TOP |
                                                   wx.BORDER_NONE)

        self.Bind(wx.EVT_CLOSE, self.OnExit)

    #-----------------------------------------------------------------------

    def OnExit(self, event):
        """
        ...
        """

        # The program will freeze without this line.
        event.Skip()  # Make sure the default handler runs too...
        self.Hide()



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

        self.new_event_acq, self.id_evt_acq = wx.lib.newevent.NewEvent() # lorsque buffer d'acquisition est plein
        self.new_event_gen, self.id_evt_gen = wx.lib.newevent.NewEvent() # lorsqu'un signal est généré
        self.parent = parent
        self.init_interface = False
        self.menu_periph_in =  None
        self.menu_periph_out =  None
        self.idmenu_audio_in = {-1: -1}
        self.idmenu_audio_out = {-1: -1}
        self.idx_periph_in = -1
        self.idx_periph_out = -1
        self.dico_slider = None
        self.dico_label = None
        self.ctrl = None
        self.ind_fichier = 0
        self.ind_page = 0
        self.duration = -1
        self.flux_audio = fluxaudio.FluxAudio((self.new_event_acq, self.new_event_gen))
        self.flux_audio_ref = None
        self.oscilloscope = None
        self.frame_gen_sig = None
        self.log = LogOscillo(self, "Oscilloscope Logger", show=False, passToOld=False)
        self.sheet =  audio.grid_frequency.GridFrequency(self, pos=(0,280))

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
                            'dpss': ('NW (normalize)', None), # 'dpss': ('NW', 'Kmax', 'norm', None),
                            'chebwin': ('at', None),
                            'exponential': ('tau', 'center (normalize)', None),
                            'tukey': ('alpha', None)}
        # nom_parametre:(type, valeur actuelle, valeur minimale, valeur maximale)
        self.dico_parameter = {'beta': ('float', 14, 0, np.PINF, False),
                               'std': ('float', 1, 0, np.PINF, True),
                               'p': ('float', 1, 0, np.PINF, False),
                               'sig': ('float', 1, 0, np.PINF, False),
                               'NW (normalize)': ('float', 0.25, 0, 0.5, True),
                               'Kmax': ('float', 1, 0, np.PINF, False),
                               'norm': ('list', (2, 'approximate', 'subsample'), False),
                               'at': ('float', 100, 0, np.PINF, False),
                               'tau': ('float', 100, 0, np.PINF, False),
                               'center (normalize)': ('float', 0.5, 0, np.PINF, True),
                               'alpha': ('float', 0.5, 0, np.PINF, False),

                               }
        self.flux_audio.type_window = self.type_window[0]
        self.choix_freq =  None # liste de choix pour les fréquences
        self.choix_palette = None # liste des palettes disponibles pour l'affichage du spectrogramme
        self.samp_in_progress = False
        self.prepare_acquisition()

    def prepare_acquisition(self, nom_periph_in=None):
        dlg = wx.ProgressDialog("Scanning audio device",
                               "",
                               maximum = len(self.idmenu_audio_in),
                               parent=None,
                               style = wx.PD_APP_MODAL
                                )
        if nom_periph_in is None:
            nb_freq = 0
            idx_best = -1
            name_best = None
            for idx, nom_periph_in in enumerate(self.idmenu_audio_in):
                dlg.Update(idx, nom_periph_in)
                self.idx_periph_in = self.idmenu_audio_in[nom_periph_in]
                nb = self.flux_audio.capacite_periph_in(self.liste_periph, self.idx_periph_in)
                if nb > nb_freq:
                    nb_freq = nb
                    name_best = nom_periph_in
                    idx_best = idx
            self.menu_periph_in.Check(idx_best+200, True)
        else:
            idx_best = self.idmenu_audio_in[nom_periph_in]
            name_best = nom_periph_in
        dlg.Destroy()
        self.idx_periph_in = idx_best
        self.flux_audio.capacite_periph_in(self.liste_periph, self.idx_periph_in)
        self.flux_audio.nb_canaux = 1 # forcer à 1 pour audiocallback_inself.liste_periph[self.idx_periph_in]["max_input_channels"]
        self.flux_audio.set_frequency(self.liste_periph[self.idx_periph_in]["default_samplerate"])
        if not self.init_interface:
            self.interface_acquisition()
            self.init_interface = True
        if self.oscilloscope:
            self.oscilloscope.page['time'].t_beg = self.flux_audio.taille_buffer_signal - self.flux_audio.nb_ech_fenetre
            self.oscilloscope.page['time'].t_end = self.flux_audio.taille_buffer_signal
        if self.choix_freq is not None:
            self.maj_choix_freq()
        wx.LogMessage("Channel : " + str(self.flux_audio.nb_canaux) + " Buffer : " + str(self.flux_audio.taille_buffer_signal))
        if self.oscilloscope:
            self.oscilloscope.maj_limite_slider()



    def select_audio_in(self, event):
        """
        fonction appelée lorsqu'un périphérique
        est sélectionné dans le menu audio_in :
        ouverture du périphérique, 
        activation de l'interface d'acquisition et
        ajout d'une marque sur l'article sélectionné
        """
        obj = event.GetEventObject()
        self.disable_item_check(1)
        id_fenetre = event.GetId()
        obj.Check(id_fenetre, True)
        nom_periph_in = obj.GetLabel(id_fenetre)
        self.prepare_acquisition(nom_periph_in)

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
        activation ou désactivation de la sortie d'acquisition et
        ajout ou retrait d'une marque sur l'article sélectionné
        """
        obj = event.GetEventObject()
        id_fenetre = event.GetId()
        nom_periph_out = obj.GetLabel(id_fenetre)
        if self.idx_periph_out == self.idmenu_audio_out[nom_periph_out]:
            self.disable_item_check(2)
            self.idx_periph_out = -1
            self.flux_audio.stream_out = None
            return
        self.disable_item_check(2)
        obj.Check(id_fenetre, True)
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
        self.ctrl = [] # liste contenant les listes des contrôles ajoutés dans chaque onglet
        self.dico_label = {0: ('Enable', 'Disable', 'time')}
        self.dico_slider = {0: None}
        self.ind_page = 0
        self.ajouter_page_acquisition()
        self.ajouter_page_tfd("Spectrum")
        self.ajouter_page_spectrogram("Spectrogram")
        self.ajouter_page_parameters("Parameters")
        self.note_book.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.close_page)
        self.note_book.Refresh(True)
        self.note_book.SetSize(self.parent.GetClientSize())
        frame = wx.Frame(None, -1,
                         'Oscilloscope',
                         pos=(650,0), size=(800,800),
                         style=wx.DEFAULT_FRAME_STYLE &
                         (~wx.CLOSE_BOX) &
                         (~wx.MAXIMIZE_BOX))
        self.oscilloscope = fc.Oscilloscope(frame,
                                            self.flux_audio,
                                            evt_type=(self.id_evt_acq, self.id_evt_gen))
        _ = self.oscilloscope.add('Time Signal', type_courbe='time')
        _ = self.oscilloscope.add('Spectrum Module', type_courbe='dft_modulus')
        _ = self.oscilloscope.add('Spectrogram', type_courbe='spectrogram')
        _ = self.oscilloscope.add('Frequency response', type_courbe='Frequency response')
        _ = self.oscilloscope.add('Spectrum Phase', type_courbe='dft_phase')
        if self.sheet is not None:
            self.sheet.set_oscilloscope(self.oscilloscope)
        self.flux_audio.courbe = self.oscilloscope
        self.oscilloscope.set_interface(self)
        frame.Show()


    def install_menu(self):
        """
        Installation des menus
        Les menus input device et output device sont construits
        à partir des listes des périphériques d'éntrée et de sortie obtenues
        par soundevice
        """
        self.liste_periph = self.flux_audio.get_device()
        self.idmenu_audio_in = {-1: -1}
        self.idmenu_audio_in = {x['name'] + ':' + sd.query_hostapis(x['hostapi']) ['name']: idx
                                for idx, x in enumerate(self.liste_periph)
                                if x['max_input_channels'] >= 1}
        self.idmenu_audio_out = {-1: -1}
        self.idmenu_audio_out = {x['name']: idx
                                 for idx, x in enumerate(self.liste_periph)
                                 if x['max_output_channels'] >= 1}
        barre_menu = wx.MenuBar()
        menu_fichier = wx.Menu()
        _ = menu_fichier.Append(wx.ID_OPEN, 'Open', "open wave file")
        _ = menu_fichier.Append(ID_OPEN_REF, 'Open reference', "open wave file")
        _ = menu_fichier.Append(wx.ID_SAVE, 'Save', "save wave file")
        _ = menu_fichier.Append(wx.ID_EXIT, 'Quit', "exit program")
        barre_menu.Append(menu_fichier, '&File')
        _ = wx.Menu()
        self.menu_periph_in = wx.Menu()
        self.idmenu_perih = {-1: -1}
        self.liste_periph_in = [self.menu_periph_in.AppendCheckItem(idx+200, x)
                                for idx, x in enumerate(self.idmenu_audio_in)]
        barre_menu.Append(self.menu_periph_in, 'input device')

        self.menu_periph_out = wx.Menu()
        self.liste_periph_out = [self.menu_periph_out.AppendCheckItem(idx+300, x)
                                 for idx, x in enumerate(self.idmenu_audio_out)]
        barre_menu.Append(self.menu_periph_out, 'output device')
        menu_tool = wx.Menu()
        _ = menu_tool.Append(ID_ZEROPADDING, 'Zero padding', 'Zero padding')
        _ = menu_tool.Append(ID_ZEROPADDING_CENTER, 'Zero padding center', 'Zero padding center')
        barre_menu.Append(menu_tool, '&Spectrum Tools')
        menu_tool = wx.Menu()
        _ = menu_tool.Append(ID_SIGGEN, 'Signal generators', 'Signal generators')
        _ = menu_tool.Append(ID_WAVMP3WAV, 'Wav to Mp3 to Wav', 'Wav to Mp3 to Wav')
        barre_menu.Append(menu_tool, '&Tools')
        menu_about = wx.Menu()
        _ = menu_about.Append(ID_LOG, 'Show log', 'Show log window')
        _ = menu_about.Append(ID_MARKER_VALUES, 'Show marker values', 'Show marker values')
        _ = menu_about.Append(wx.ID_ABOUT, 'About', 'About anaspec')
        barre_menu.Append(menu_about, '&Help')
        self.parent.SetMenuBar(barre_menu)
        self.disable_item_check(2)
        self.parent.Bind(wx.EVT_CLOSE, self.close_page)
        self.parent.Bind(wx.EVT_MENU, self.about, id=wx.ID_ABOUT)
        self.parent.Bind(wx.EVT_MENU, self.generation_sig, id=ID_SIGGEN)
        self.parent.Bind(wx.EVT_MENU, lambda evt: audio.mp3_wav.wav_mp3_wav(evt, self), id=ID_WAVMP3WAV)
        self.parent.Bind(wx.EVT_MENU, self.zero_padding, id=ID_ZEROPADDING)
        self.parent.Bind(wx.EVT_MENU, self.zero_padding, id=ID_ZEROPADDING_CENTER)
        self.parent.Bind(wx.EVT_MENU, self.show_log, id=ID_LOG)
        self.parent.Bind(wx.EVT_MENU, self.show_marker_values, id=ID_MARKER_VALUES)
        self.parent.Bind(wx.EVT_MENU, self.open_wav, id=wx.ID_OPEN)
        self.parent.Bind(wx.EVT_MENU, self.open_wav_ref, id=ID_OPEN_REF)
        self.parent.Bind(wx.EVT_MENU, self.on_save, id=wx.ID_SAVE)
        self.parent.Bind(wx.EVT_MENU, self.quitter, id=wx.ID_EXIT)
        self.parent.Bind(wx.EVT_MENU, self.select_audio_in, id=200, id2=299)
        self.parent.Bind(wx.EVT_MENU, self.select_audio_out, id=300, id2=399)

    def generation_sig(self, evt):
        """
        Génération se signaux
        """
        if self.flux_audio.plotdata is None:
               wx.MessageBox("First choose peripherical in input device menu", "Error", wx.ICON_ERROR)
               return
        if self.frame_gen_sig is None:
            self.frame_gen_sig = wx.Frame(None, -1, 'Signal generators', pos=(0,280), size=(660,520))
            gen_sig = generation_signal.InterfaceGeneration(self.frame_gen_sig, fa=self.flux_audio)
            gen_sig.interface_generation_fct()
            self.frame_gen_sig.Bind(wx.EVT_CLOSE, self.hide_gen_sig)
            my_frame.Show()
        else:
            self.frame_gen_sig.Show(True)
            
    def hide_gen_sig(self, evt):
        """
        on clicl close box hide windows  self.frame_gen_sig 
        """
        if self.frame_gen_sig is not None:
            self.frame_gen_sig.Show(False)

    def zero_padding(self, event):
        """
        zero padding
        https://dsp.stackexchange.com/questions/741/why-should-i-zero-pad-a-signal-before-taking-the-fourier-transform
        """
        if self.flux_audio.plotdata is None:
               wx.MessageBox("First choose peripherical in input device menu", "Error", wx.ICON_ERROR)
               return
        if event.GetId() == ID_ZEROPADDING:
            self.flux_audio.zero_padding(center=False)
        else:
            self.flux_audio.zero_padding(center=True)
        self.oscilloscope.set_t_max(self.flux_audio.taille_buffer_signal)
        self.oscilloscope.set_t_beg(0)
        self.oscilloscope.set_t_end(self.flux_audio.taille_buffer_signal)
        self.oscilloscope.maj_limite_slider()
        


    def about(self, evt):
        """
        About menu
        """
        wx.MessageBox("Anaspec : https://github.com/LaurentBerger/anaspec")

    def hide_log(self, evt):
        """
        log menu to show log window
        """
        if self.log is not None:
            self.log.Show(False)

    def show_log(self, evt):
        """
        log menu to show log window
        """
        if self.log is None:
            self.log = wx.LogWindow(None, "Oscilloscope Logger", show=True, passToOld=False)
        else:
            self.log.Show(True)

    def show_marker_values(self, evt):
        """
        menu to show grid
        """
        if self.sheet is None:
            self.sheet =  audio.grid_frequency.GridFrequency(self)
        else:
            self.sheet.Show(True)

    def close_page(self, evt):
        """
        surchage de close pour interdire
        la fermeture des onglets
        """
        wx.MessageBox("Cannot be closed. Use File menu to quit", "Warning", wx.ICON_WARNING)
        evt.Veto()

    def open_wav_ref(self, _):
        """
        ouvrir un fichier wav et utiliser les données 
        comme l'entrée appliquée à un système
        """
        if self.flux_audio.plotdata is None:
               wx.MessageBox("First choose peripherical in input device menu", "Error", wx.ICON_ERROR)
               return
        nom_fichier_son = wx.FileSelector("Open wave file reference",wildcard="*.wav")
        if nom_fichier_son.strip():
            son , Fe = soundfile.read(nom_fichier_son)
            if self.flux_audio.Fe != Fe:
                wx.MessageBox("Sampling frequency are not equal\n "+ str(self.flux_audio.Fe) + "Hz<> " +str(Fe), "Error", wx.ICON_ERROR)
                return
            self.flux_audio_ref = fluxaudio.Signal(freq=Fe, fenetre=son.shape[0], canaux=len(son.shape), s_array=son, file_name=nom_fichier_son)
            self.oscilloscope.page['time'].flux_audio_ref = self.flux_audio_ref
            self.oscilloscope.page['dft_modulus'].flux_audio_ref = self.flux_audio_ref
            self.oscilloscope.page['spectrogram'].flux_audio_ref = self.flux_audio_ref
            self.oscilloscope.page['Frequency response'].flux_audio_ref = self.flux_audio_ref
            self.flux_audio_ref.compute_spectrum()
            wx.LogMessage("File name (ref): " + nom_fichier_son)
            wx.LogMessage("Sample size (ref): " + str(son.shape))
            wx.LogMessage("Sample size (sig): " + str(self.flux_audio.plotdata.shape))
            wx.LogMessage("Sample size (sig) selected: " + str(self.oscilloscope.page['time'].t_beg) +
                          " " + str(self.oscilloscope.page['time'].t_end))
 
    def open_wav(self, _):
        """
        ouvrir un fichier wav et utiliser les données 
        de la même manière que l'acquisition
        """
        if self.flux_audio.plotdata is None:
            wx.MessageBox("First choose peripherical in input device menu", "Error", wx.ICON_ERROR)
            return
        nom_fichier_son = wx.FileSelector("Open wave file",wildcard="*.wav")
        if nom_fichier_son.strip():
            self.set_window_size()
            son , Fe = soundfile.read(nom_fichier_son)
            if str(float(Fe)) not in self.flux_audio.frequence_dispo:
                wx.MessageBox("Sampling not available\nTry to change audio device in "+ str(self.flux_audio.Fe) + "Hz<> " +str(Fe), "Error", wx.ICON_ERROR)
                return
            self.flux_audio.set_frequency(Fe)
            self.maj_choix_freq()
            nb_ech = son.shape[0]
            self.oscilloscope.set_t_max(nb_ech)
            self.oscilloscope.set_t_beg(0)
            self.oscilloscope.set_t_end(nb_ech)
            self.flux_audio.init_data_courbe(nb_ech)
            self.oscilloscope.maj_limite_slider()
            if len(son.shape) == 1:
                self.flux_audio.plotdata[:,0] = son[:nb_ech]
            else:
                self.flux_audio.plotdata[:,0] = son[:nb_ech,0]
                if son.shape[1] != self.flux_audio.plotdata.shape[1]:
                    wx.MessageBox("Channel number are not equal. First channel uses", "Warning", wx.ICON_WARNING)
                elif son.shape[1] == 2:
                    self.flux_audio.plotdata[self.flux_audio.plotdata.shape[0]-nb_ech:,1] += son[:nb_ech,1] 
            # self.flux_audio.nb_ech_fenetre = nb_ech 
            # wx.MessageBox("Update sampling modified\n New value "+str(nb_ech), "Warning", wx.ICON_WARNING)
            # w = wx.Window.FindWindowById(UPDATE_ECH)
            # w.SetLabel(str(self.flux_audio.nb_ech_fenetre))
            wx.LogMessage("File name : " + nom_fichier_son)
            wx.LogMessage("Sample size " + str(son.shape))
            wx.LogMessage("Sample size (sig) " + str(self.flux_audio.plotdata.shape))
            wx.LogMessage("Sample selected" + str(self.oscilloscope.page['time'].t_beg) + 
                          " " + str(self.oscilloscope.page['time'].t_end))
            self.oscilloscope.page['time'].courbe_active = True
            self.oscilloscope.draw_all_axis()
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
                                 'dft_modulus')
        
        bouton = wx.Button(page, id=2000, label='Enable plot spectrum')
        bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
        bouton.Bind(wx.EVT_BUTTON, self.on_enable_graphic, bouton)
        self.ajouter_bouton((bouton, 0), ctrl, ma_grille, font)
        st_texte = wx.StaticText(page, label="")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)

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

    def ajouter_page_parameters(self, name="Parameters"):
        """
        création de l'onglet Parameters
        pour paramétrer la hauteur où est mesurée
        la bande passante et l'espacement entre les pics pour
        la détection des pics
        """
        ctrl = []
        page = wx.Panel(self.note_book)
        font = wx.Font(10,
                       wx.FONTFAMILY_DEFAULT,
                       wx.FONTSTYLE_NORMAL,
                       wx.FONTWEIGHT_BOLD)
        ma_grille = wx.GridSizer(rows=5, cols=2, vgap=5, hgap=5)

        st_texte = wx.StaticText(page, label="Bandwidth at (dB)")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)
        style_texte = wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_MIN_MAX_LABELS
        st_texte = wx.Slider(page,
                             id=SLIDER_BP_VALUE,
                             value=-3,
                             minValue=-10,
                             maxValue=-1,
                             style=style_texte,
                             name="Bandwidth")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)
        st_texte.Bind(wx.EVT_SCROLL_CHANGED,
                      self.change_slider,
                      st_texte,
                      SLIDER_BP_VALUE)
        self.dico_slider[SLIDER_BP_VALUE] = (self.flux_audio.set_bp_level, None)

        st_texte = wx.StaticText(page, label="Distance in samples between neighbouring peaks")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)
        st_texte = wx.Slider(page,
                             id=SLIDER_PEAK_DISTANCE,
                             value=1,
                             minValue=1,
                             maxValue=1000,
                             style=style_texte,
                             name="PeakDistance")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)
        st_texte.Bind(wx.EVT_SCROLL_CHANGED,
                      self.change_slider,
                      st_texte,
                      SLIDER_PEAK_DISTANCE)
        self.dico_slider[SLIDER_PEAK_DISTANCE] = (self.flux_audio.set_peak_distance, None)
        # https://dsp.stackexchange.com/questions/36018/dont-window-a-transient-signal
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
            self.flux_audio.type_window))
        st_texte.Bind(wx.EVT_COMBOBOX,
                      self.change_fenetrage,
                      st_texte,
                      COMBO_WINDOW_TYPE)
        self.nb_parametre_max = 3
        presentation_parametre = wx.GridSizer(rows=self.nb_parametre_max, cols=2, vgap=5, hgap=5)
        for idx in range(self.nb_parametre_max):
            st_texte = wx.StaticText(page, id=PARAM1_WINDOW_TYPE + 2*idx, label="")
            presentation_parametre.Add(st_texte)
            if idx < 2:
                new_ctrl = wx.TextCtrl(page,
                                       id=PARAM1_WINDOW_TYPE+1+ 2*idx,
                                       value=str(0),
                                       style=wx.TE_PROCESS_ENTER)
                new_ctrl.Bind(wx.EVT_TEXT,
                              self.update_fenetrage_num,
                              new_ctrl,
                              PARAM1_WINDOW_TYPE+1+ 2*idx)
            else:
                new_ctrl = wx.Choice(page, id=PARAM1_WINDOW_TYPE+1+ 2*idx, choices=[])
                new_ctrl.Bind(wx.EVT_TEXT,
                              self.update_fenetrage_list,
                              new_ctrl,
                              PARAM1_WINDOW_TYPE+1+ 2*idx)
            presentation_parametre.Add(new_ctrl)
        self.change_param_window()
        ma_grille.Add(presentation_parametre)
    


        page.SetSizerAndFit(ma_grille)
        self.note_book.AddPage(page, name)
        self.ctrl.append(ctrl)
        self.ind_page = self.ind_page + 1


    def update_fenetrage_list(self, event):
        """
        Changement du choix pour les paramètres
        d'une fenêtre
        INUTILISER
        """
        id_fenetre = event.GetId()
        obj = event.GetEventObject()
        val = obj.GetValue()
        if id_fenetre == PARAM1_WINDOW_TYPE+5:
            self.flux_audio.type_window[2] = val
            self.change_param_window()


    def update_fenetrage_num(self, event):
        """
        une valeur des paramètres a été chnagée
        """
        id_fenetre = event.GetId()
        obj = event.GetEventObject()
        val = obj.GetValue()
        try:
            val_num = float(val)
        except ValueError as e:
            wx.LogError(val + " is not a number")
            return
        param = self.dico_window[self.flux_audio.type_window[0]]
        if param is None:
            wx.LogError("Should not happen in update_fenetrage for dico")
            return
        try:
            if id_fenetre == PARAM1_WINDOW_TYPE+1: # premier parametre
                param_ctrl = self.dico_parameter[param[0]]
                if param_ctrl[2] <= val_num <= param_ctrl[3]:
                    p = (param_ctrl[0], val_num, param_ctrl[2], param_ctrl[3])
                    self.dico_parameter[param[0]] = p
                    win_para = self.flux_audio.type_window
                    self.flux_audio.type_window[1] = val_num
            elif id_fenetre == PARAM1_WINDOW_TYPE+3: # second parametre
                param_ctrl = self.dico_parameter[param[1]]
                if param_ctrl[2] <= val_num <= param_ctrl[3]:
                    p = (param_ctrl[0], val_num, param_ctrl[2], param_ctrl[3])
                    self.dico_parameter[param[1]] = p
                    self.flux_audio.type_window[2] = val_num
            else:
                wx.LogError("Should not happen in update_fenetrage")
                return
        except ValueError as e:
            wx.LogError("Should not happen in update_fenetrage for dico_parameter")
            return

    def change_fenetrage(self, event):
        """
        Changement du type de fenêtre pour la tfd et
        le spectrogramme
        """
        id_fenetre = event.GetId()
        obj = event.GetEventObject()
        val = obj.GetValue()
        if id_fenetre == COMBO_WINDOW_TYPE:
            self.flux_audio.type_window = [val]
            self.change_param_window()

    def change_param_window(self):
        """
        Activation ou désactivation des articles des 
        paramètres du fenêtrage en
        fonction de la fenêtre spectrale
        """
        if self.flux_audio.type_window[0] not in self.dico_window:
            return
        for idx in range(0, 2*self.nb_parametre_max):
            fen = wx.Window.FindWindowById(idx + PARAM1_WINDOW_TYPE)
            if fen is not None:
                fen.Enable(False)
                fen.Show(False)
        """        
        fen = wx.Window.FindWindowById(PARAM1_WINDOW_TYPE-1)
        if fen is not None:
            fen.Enable(False)
            fen.Show(False)
        fen = wx.Window.FindWindowById(PARAM2_WINDOW_TYPE-1)
        if fen is not None:
            fen.Enable(False)
            fen.Show(False)
        """
        param = self.dico_window[self.flux_audio.type_window[0]]
        idx_param = 0
        while param is not None and param[idx_param] is  not None:
            for idx in range(0, 2):
                fen = wx.Window.FindWindowById(idx_param*2 + PARAM1_WINDOW_TYPE + idx)
                if fen is not None:
                    fen.Enable(True)
                    fen.Show(True)
                if idx == 0:
                    fen.SetLabel(param[idx_param])
                else:
                    try:
                        x = self.dico_parameter[param[idx_param]]
                        self.flux_audio.type_window.append(x)
                        if x[0] != 'list':
                            fen.SetValue(str(x[1]))
                        else:
                            wx.LogError("parameter list not implemented") 
                    except KeyError as e:
                        wx.LogError("Should not happen with window parameter")     
            idx_param =  idx_param + 1

    def ajouter_page_acquisition(self, name="Sampling"):
        """
        création de l'onglet Sampling
        pour paramétrer la fréquence d'acquisition et
        le temps de rafraichissment de l'oscilloscope
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

        """
        st_texte = wx.StaticText(page,
                                 label="recording Time (-1 for infinite)")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)

        st_texte = wx.TextCtrl(page, value="-1", id=RECORDING_TIME)
        self.ajouter_bouton((st_texte, 1), ctrl, ma_grille, font)
        """

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
        """
        Mise à jour des fréquences d'acquition
        disponibles lors du choix du périphérique d'entrée
        """
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
        """
        Mise à jour des extrêmums des glissières de la sélection
        des fréquences en fonction de la fréquence d'échantillonnage
        """
        idx = self.choix_freq.GetCurrentSelection()
        chaine_freq = self.choix_freq.GetString(idx)
        self.flux_audio.set_frequency(float(chaine_freq))
        self.oscilloscope.maj_limite_slider()
        self.update_spectro_interface()
        self.update_tfd_interface()
        self.oscilloscope.draw_all_axis()

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
                                 'spectrogram')
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

        st_texte = wx.StaticText(page, label="Palette")
        self.ajouter_bouton((st_texte, 0), ctrl, ma_grille, font)
        choix = []
        palette_name = sorted(PALETTE_NAME)
        for name_p in palette_name:
            choix.append(name_p)
        self.choix_palette = wx.Choice(page, choices=choix)
        idx = self.choix_palette.FindString("grey")
        if idx !=  wx.NOT_FOUND:
            self.choix_palette.SetSelection(idx)
        else:
            self.choix_palette.SetSelection(0)
        self.choix_palette.Bind(wx.EVT_CHOICE, self.maj_palette)
        self.ajouter_bouton((self.choix_palette, 1), ctrl, ma_grille, font)
        page.SetSizerAndFit(ma_grille)
        self.note_book.AddPage(page, name)
        self.ctrl.append(ctrl)
        self.ind_page = self.ind_page + 1


    def maj_palette(self, evt):
        """
        Mise à jour de la palette
        pour l'affichage du spectrogramme
        """
        idx = self.choix_palette.GetCurrentSelection()
        pal_name = self.choix_palette.GetString(idx)
        self.oscilloscope.maj_palette("spectrogram", pal_name)



    def change_slider(self, event):
        """
        Réglage des glissiéres et
        mise à jour des fenêtres
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
        if self.dico_slider[id_fenetre][1] is not None:
            self.oscilloscope.draw_all_axis()
            r_upd = self.oscilloscope.GetClientRect()
            self.oscilloscope.Refresh(rect=r_upd)
            if not self.samp_in_progress and self.dico_slider[id_fenetre][1] is not None:
                self.oscilloscope.maj_page(self.dico_slider[id_fenetre][1])

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
        if self.oscilloscope.page[1].courbe_active:
            self.oscilloscope.draw_all_axis()
            r_upd = self.oscilloscope.GetClientRect()
            self.oscilloscope.Refresh(rect=r_upd)
        if not self.samp_in_progress:
            self.oscilloscope.maj_page(self.dico_slider[SLIDER_F_MAX_TFD][1])


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
        if self.oscilloscope.page[2].courbe_active:
            self.oscilloscope.draw_all_axis()
            r_upd = self.oscilloscope.GetClientRect()
            self.oscilloscope.Refresh(rect=r_upd)
            print("refresh")
        if not self.samp_in_progress:
            self.oscilloscope.maj_page(self.dico_slider[SLIDER_F_MAX_SPECTRO][1])
 


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
            self.oscilloscope.maj_page('spectrogram') 

    def update_tfd_interface(self):
        low = wx.Window.FindWindowById(SLIDER_F_MIN_TFD)
        if low:
            low.SetMax(int(self.flux_audio.set_frequency()//2))
        high = wx.Window.FindWindowById(SLIDER_F_MAX_TFD)
        if high:
            high.SetMax(int(self.flux_audio.set_frequency()//2))
        self.oscilloscope.draw_all_axis()
        if not self.samp_in_progress:
            self.oscilloscope.maj_page("spectrogram")

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
        texte_article = self.ctrl[0][5][0].GetValue()
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
        INUTILISER PLUS  D ARTICLE
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
            self.oscilloscope.page[ind_page].courbe_active = True
            self.oscilloscope.draw_all_axis()

        else:
            print("DesActivation courbe")
            bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
            bouton.SetLabel(self.dico_label[id_fenetre][0])
            self.oscilloscope.page[ind_page].courbe_active = False

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
        Ecoute du signal enregistré
        """
        print("try to play on default output")
        try:            
            sd.play(self.flux_audio.plotdata[self.oscilloscope.page['time'].t_beg:self.oscilloscope.page['time'].t_end, :],
                    self.flux_audio.Fe, mapping=[1, 2])
        except Exception as e:
            wx.LogError("Cannot play signal :\n" + str(e) )        


    def on_start_stop(self, event):
        """
        Défut/Fin de l'acquisition
        """
        if self.idmenu_audio_in is None:
            wx.MessageBox("You must select an audio in device",
                          "Warning",
                          wx.ICON_WARNING)
            return
        bouton = event.GetEventObject()
        texte_label = bouton.GetLabel()
        if texte_label == "Start":
            idx = self.choix_freq.GetCurrentSelection()
            chaine_freq = self.choix_freq.GetString(idx)
            self.flux_audio.set_frequency(int(float(chaine_freq)))
            self.set_window_size()
            # self.set_time_length()
            self.oscilloscope.draw_all_axis()
            if not self.flux_audio.open_stream_in(self.idx_periph_in):
                self.disable_item_check()
                wx.MessageBox("Cannot opened input device : input disable",
                              "Error",
                              wx.ICON_WARNING)
                return
            if self.idx_periph_out != -1:
                self.flux_audio.open_stream_out(self.idx_periph_out)
            self.update_spectro_interface()
            self.update_tfd_interface()
            for name in self.oscilloscope.page:
                self.oscilloscope.page[name].samp_in_progress = False
            self.oscilloscope.page['time'].courbe_active = True
            bouton.SetLabel("Stop")
            bouton.SetBackgroundColour(wx.Colour(255, 0, 0))
            self.figer_parametre(True)
            self.samp_in_progress = True
        else:
            self.flux_audio.close()
            self.oscilloscope.page['time'].courbe_active = False
            bouton.SetLabel("Start")
            bouton.SetBackgroundColour(wx.Colour(0, 255, 0))
            self.figer_parametre(False)
            self.samp_in_progress = False
            for name in self.oscilloscope.page:
                self.oscilloscope.page[name].samp_in_progress = False

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
    MySplash = MySplashScreen()
    # MySplash.CenterOnScreen(wx.BOTH)
    MySplash.Show(True)


    my_frame = wx.Frame(None, -1, 'Interface',pos=(0,0), size=(660,280))
    my_plotter = InterfaceAnalyseur(my_frame)
    my_frame.Show()
    
    wx.LogWarning("Disbale quick-edit mode in console")
    disable_quick_edit_mode()
    wx.LogWarning("First choose peripherical in input device menu")

    application.MainLoop()
