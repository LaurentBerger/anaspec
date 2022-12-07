"""
===========
Slider Demo
===========

Using the slider widget to control visual properties of your plot.

In this example, a slider is used to choose the frequency of a sine
wave. You can control many continuously-varying properties of your plot in
this way.
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons
from scipy import signal
import soundfile as sf
import sounddevice as sd

import wx

def update_tobs(val):
    tobs = sl_tobs.val
    sl_orig.valmax = N / Fe - tobs
    sl_orig.ax.set_xlim(0,sl_orig.valmax)
    update(0)

def update_orig(val):
    orig = sl_orig.val
    sl_tobs.valmax = N / Fe - orig
    sl_tobs.ax.set_xlim(0,sl_tobs.valmax)
    update(0)

def update(val):
    global choix_fenetre
    der_tobs = sl_tobs.val
    der_orig = sl_orig.val
    k_orig = int(der_orig * Fe)
    nb_l = int (der_tobs * Fe)
    fenetre = np.zeros(N)
    fenetre[k_orig: k_orig + nb_l] = son.max()
    courbe_fenetre.set_ydata(fenetre)
    if len(son.shape) == 1:
        signal = son[k_orig:min(N, k_orig + nb_l)]
    else:
        signal = son[k_orig:min(N, k_orig + nb_l), :]
    freq = np.fft.fftfreq(nb_l)*Fe
    #ma_courbe_tempo.set_ydata(signal)
    S = np.fft.fft(signal)
    ma_courbe_freq.set_data(np.fft.fftshift(freq),np.fft.fftshift(np.abs(S).real/Fe))
    fig.canvas.draw_idle()

def reset(event):
    sl_orig.reset()
    sl_tobs.reset()

def change_fenetre(label):
    global choix_fenetre
    choix_fenetre = label
    update(0)

def annule_extreme(signal, freq_ech, duree_obs):
    nb_zero = int((signal.shape[0] / Fe - duree_obs)* Fe)
    if nb_zero == 0:
        return signal
    signal[0:nb_zero//2] = 0
    signal[-nb_zero//2:] = 0
    return signal


if __name__ == '__main__':
    my_app = wx.App()
    nom_fichier_son = wx.FileSelector("Fichier son",wildcard="*.wav")
    son , Fe = sf.read(nom_fichier_son)
    N = son.shape[0]
    if len(son.shape) == 2:
        son = son[:,0]
    print("Nombre d'échantillons : ", N)
    print("Fréquence d'échantillonnage : ", Fe)
    S = np.fft.fft(son, axis=0)
    if len(son.shape) == 1:
        nb_courbe = 1
    else:
        nb_courbe = son.shape[1]
    fenetre_active = { 'Rectangulaire':signal.boxcar,
                       'Hamming':signal.hamming,
                       'blackman':signal.blackman}
    fig, ax = plt.subplots(nrows=2, ncols=1)
    plt.subplots_adjust(left=0.25, bottom=0.25)
    te = np.arange(0,N)/Fe
    ma_courbe_tempo,  = ax[0].plot(te,son,label='x(t)', lw=2)
    axcolor = 'lightgoldenrodyellow'
    ax_orig = plt.axes([0.25, 0.1, 0.65, 0.03], facecolor=axcolor)
    ax_tobs = plt.axes([0.25, 0.15, 0.65, 0.03], facecolor=axcolor)
    der_orig = 0
    der_tobs = N / Fe
    sl_tobs = Slider(ax_tobs, 'T_Obs', 0, N/Fe, valinit=der_tobs, valstep=N/ Fe / 20)
    sl_orig = Slider(ax_orig, 'Origine', 0., N/Fe-der_tobs, valinit=der_orig, valstep=N/ Fe / 20)
    fenetre = np.zeros(N)
    fenetre[int(der_orig * Fe):int(der_orig * Fe)+int(der_tobs * Fe)] = son.max()
    courbe_fenetre, = ax[0].plot(te,fenetre,color='red',label='fenetre')
    ax[0].grid(True)
    delta_f = 1.0
    ax[0].margins(x=0)
    ax[0].set(xlabel='t (s)', ylabel='f(t)) (u.a.)')
    freq = np.fft.fftfreq(N)*Fe
    S = np.fft.fft(son)
    ma_courbe_freq, = ax[1].plot(np.fft.fftshift(freq),np.fft.fftshift(np.abs(S).real/Fe), label=r"$ |X(\nu)| $")
    ax[1].grid(True)
    ax[1].set(xlabel=r'$ \nu (Hz) $', ylabel='(u.a.)')
    ax[0].legend()
    ax[1].legend()
    sl_orig.on_changed(update_orig)
    sl_tobs.on_changed(update_tobs)

    reset_ax = plt.axes([0.8, 0.025, 0.1, 0.04])
    button = Button(reset_ax, 'Reset', color=axcolor, hovercolor='0.975')
    button.on_clicked(reset)

    plt.show()
