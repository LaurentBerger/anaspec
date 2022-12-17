import numpy as np
import soundfile as sf
import sounddevice as sd
import scipy.signal
from matplotlib import pyplot as plt
import wx

class WavAnalysis:
    def __init__(self, file_name):
        self.son , self.Fe = sf.read(file_name)
        t_ech = np.arange(0,self.son.shape[0])*1/self.Fe
        self.fig1 = None
        self.fig2 = None
        self.fig3 = None
        self.ax1 = None
        self.ax2 = None
        self.ax3 = None
        self.freq = None
        self.y = None
        self.Y = None
        self.val_freq = None
        self.val_mod = None
        self.nb_courbe = 0
        self.peak_mark = None
        self.bp_line = None

    def init_signal(self):
        self.N = self.son.shape[0]
        print("Nombre d'échantillons : ", self.N, self.son.shape)
        print("Fréquence d'échantillonnage : ", self.Fe)
        if len(self.son.shape) == 1:
            self.nb_courbe = 1
        else:
            print("Son stéréophonique")
            print("Voulez vous conserver la voie 0, 1 ou garder les deux?")
            l_choix = ["0", "1", "2"]
            choix = ''
            while choix not in l_choix:
                choix = input("Votre choix 0, 1 ou 2")
            match choix:
                case "0":
                    print("Extraction de la voie 0 pour analyse")
                    self.son = self.son[:,0]
                    self.nb_courbe = 1
                case "1":
                    print("Extraction de la voie 1 pour analyse")
                    self.son = self.son[:,1]
                    self.nb_courbe = 1
                case _:
                    print("Analyse des deux voies")
                    self.nb_courbe = 2
        print("Nombre de voies : ", self.nb_courbe)
        print("Nombre d'échantillons : ", self.N, self.son.shape)
        self.S = np.fft.fft(self.son, axis=0)

    def run(self):    
        # Tracer du signal temporel
        self.fig1, self.ax1 = plt.subplots(nrows=1, ncols=self.nb_courbe)
        self.fig2, self.ax2 = plt.subplots(nrows=1, ncols=self.nb_courbe)
        self.fig3, self.ax3 = plt.subplots(nrows=1, ncols=self.nb_courbe)
        self.te = np.arange(0,self.N)/self.Fe
        self.freq = np.fft.fftfreq(self.N)*self.Fe
        for idx_voie in range(0,self.nb_courbe):
            if self.nb_courbe == 1:
                graphe1 = self.ax1
                graphe2 = self.ax2
                graphe3 = self.ax3
                self.y = self.son
                self.Y = self.S
            else:
                graphe1 = self.ax1[idx_voie]
                graphe2 = self.ax2[idx_voie]
                graphe3 = self.ax3[idx_voie]
                y = self.son[:, idx_voie]
                Y = self.S[:, idx_voie]
            graphe1.plot(self.te, self.y,label='Voie ' + str(idx_voie))
            if idx_voie == 0:
                graphe1.set(title=nom_fichier_son)
            graphe1.grid(True)
            graphe1.set(xlabel='Time (s)', ylabel=' y (u.a.)')
            graphe1.legend()
            plt.pause(0.1)
        # Tracer du module du spectre de la TFD du signal temporel
            plt.figure(2)
            self.val_freq = np.fft.fftshift(self.freq)
            self.val_mod = np.fft.fftshift(np.abs(self.Y).real/self.Fe)
            graphe2.plot(self.val_freq,
                         self.val_mod,
                         marker='.',
                         label='Voie ' + str(idx_voie))
            if idx_voie == 0:
                graphe2.set(title='Module de la T.F.D.')
            graphe2.legend()
            graphe2.grid(True)
            graphe2.set(xlabel='Fréquence (Hz)',ylabel='Amplitude (u.a.)')
        # Tracer de la phase du spectre de la TFD du signal temporel
            plt.figure(3)
            self.val_angle = np.fft.fftshift(np.angle(self.Y))
            graphe3.plot(self.val_freq,
                         self.val_angle,
                         marker='.',
                         label='Voie ' + str(idx_voie))
            if idx_voie == 0:
                graphe3.set(title='Phase de la T.F.D.')
            graphe3.legend()
            graphe3.grid(True)
            graphe3.set(xlabel='Fréquence (Hz)',ylabel='Phase (rd)')
            module_mouse =  lambda event: self.on_click_module(event, 0, (graphe2, self.fig2))
            self.fig2.canvas.mpl_connect('button_press_event', module_mouse)
            phase_mouse =  lambda event: self.on_click_module(event, 1, (graphe3,self.fig3))
            self.fig3.canvas.mpl_connect('button_press_event', phase_mouse)

        plt.show()
     
    def localise_freq(self, x, y, graphe):
        idx_freq = self.Fe / self.N
        idx_min, idx_max = graphe.get_xlim()
        idx_min = int(np.round(idx_min /idx_freq))
        idx_max = int(np.round(idx_max /idx_freq))
        idx = np.argmin(np.abs(self.val_freq-x))
        n_min = max(idx - 1000, 0)
        n_max = min(idx + 1000, self.val_freq.shape[0])
        idx = np.argmin(np.abs(y - self.val_mod[n_min : n_max])) + n_min
        return idx
    

    def on_click_module(self, event, type, graphe):
        if event.inaxes:
            idx = self.localise_freq(event.xdata, event.ydata, graphe[0])
            if event.key == 'shift':
                print('Fréquence retenue ', format(self.val_freq[idx],'.5e'), "Hz")
                if type == 0:
                    print('Module ', format(self.val_mod[idx], '.4e')," u.a.")
                if type == 1:
                    print('Phase ', format(self.val_mod[idx], '.4e')," u.a.")
            if event.key == 'alt' and type == 0:
                print('Fréquence retenue ', format(self.val_freq[idx],'.5e'), "Hz")
                print('Module ', format(self.val_mod[idx], '.4e')," u.a.")
                bp_inf = np.where(self.val_mod[idx+1:self.N//2:-1] < self.val_mod[idx]/2)
                if bp_inf[0].shape[0] > 0:
                    idx_inf = idx + 1 -bp_inf[0][0]
                else:
                    idx_inf =  self.N//2
                bp_sup = np.where(self.val_mod[idx:] < self.val_mod[idx]/2)
                print(bp_sup)
                print(bp_inf)
                if bp_sup[0].shape[0] > 0:
                    idx_sup = bp_sup[0][0]+idx
                else:
                    idx_sup =  self.N
                print(idx, idx_inf, idx_sup)
                print('Width at height ', format(self.val_mod[idx]/2, '.4e'), end='')
                print('BP = ', self.val_freq[idx_sup] - self.val_freq[idx_inf], 'Hz', end='')
                print('Uncertainty  ', format(2 * self.Fe/self.N, '.4e'), "Hz")
                if self.bp_line:
                    self.bp_line.remove()
                self.bp_line = graphe[0].hlines(self.val_mod[idx]/2, self.val_freq[idx_inf], self.val_freq[idx_sup])
            if event.key == 'control' and type == 0:
                print('Fréquence retenue ', format(self.val_freq[idx],'.5e'), "Hz")
                pos_peak, _ = scipy.signal.find_peaks(self.val_mod, height=self.val_mod[idx]/2)
                nb_peak = 0
                for p in pos_peak:                   
                    if self.val_freq[p] > 0:
                        print('F ', format(self.val_freq[p],'.5e'), "Hz",
                              'M ', format(self.val_mod[p], '.4e')," u.a.")
                        nb_peak = nb_peak + 1
                        if nb_peak>=100:
                            print("Number of peaks is greater than 100")
                            print("Stop iterating")
                            break
                if nb_peak <= 100:
                    if self.peak_mark is not None:
                        for line in self.peak_mark:
                            line.remove()
                    pos = self.val_freq[pos_peak] > 0
                    self.peak_mark = graphe[0].plot(self.val_freq[pos_peak[pos]], self.val_mod[pos_peak[pos]], "x")
                    graphe[1].canvas.draw()
                

my_app = wx.App()
nom_fichier_son = wx.FileSelector("Fichier son",wildcard="*.wav")
del my_app

x = WavAnalysis(nom_fichier_son)
x.init_signal()
x.run()
