#exec(open(r'C:\Users\berger\Desktop\anaspec.py',encoding='utf-8').read())
import sys
import numpy as np
import soundfile as sf
import sounddevice as sd
from matplotlib import pyplot as plt
import wx

def on_click_module(event, freq, mod_f):
    if event.key == 'shift':
        x, y = event.xdata, event.ydata
        idx = np.argmin(np.abs(freq-x))
        if event.inaxes:
            ax = event.inaxes  # the axes instance
            print('data coords ', x, freq[idx], mod_f[idx])


my_app = wx.App()
nom_fichier_son = wx.FileSelector("Fichier son",wildcard="*.wav")
del my_app

son , Fe = sf.read(nom_fichier_son)
N = son.shape[0]
print("Nombre d'échantillons : ", N)
print("Fréquence d'échantillonnage : ", Fe)
print("Nombre de voies : ", son.shape)
if len(son.shape) == 2:
    son = son[:,0]
    print("Passage en mono du signal")
S = np.fft.fft(son, axis=0)
nb_courbe = 1
# Tracer du signal temporel
fig1, ax_temps = plt.subplots(nrows=1, ncols=nb_courbe)
fig2, ax_module = plt.subplots(nrows=1, ncols=nb_courbe)
fig3, ax_phase = plt.subplots(nrows=1, ncols=nb_courbe)

te = np.arange(0,N)/Fe
freq = np.fft.fftfreq(N)*Fe
idx_voie = 0
y = son
Y = S
ax_temps.plot(te,y,label='Voie ' + str(idx_voie))
ax_temps.set(title=nom_fichier_son)
ax_temps.grid(True)
ax_temps.set(xlabel='Time (s)', ylabel=' y (u.a.)')
ax_temps.legend()
plt.pause(0.1)
# Tracer du module du spectre de la TFD du signal temporel
plt.figure(2)
freq = np.fft.fftshift(freq)
mod_tf = np.fft.fftshift(np.abs(Y).real/Fe)
freq_deb = 7600
freq_fin = 9900
idx = np.logical_and(freq>freq_deb, freq<freq_fin)
freq_positive =freq[idx]
mod_tf_pos = mod_tf[idx]
p =  np.polyfit(freq_positive, mod_tf_pos,15)
ax_module.plot(freq,
               mod_tf,
               marker='.',
               label='Voie ' + str(idx_voie))
ax_module.set(title='Module de la T.F.D.')
ax_module.plot(freq_positive,
             np.polyval(p, freq_positive),
             label='poly ')
ax_module.legend()
ax_module.grid(True)
ax_module.set(xlabel='Fréquence (Hz)',ylabel='Amplitude (u.a.)')
# Tracer de la phase du spectre de la TFD du signal temporel
plt.figure(3)
ax_phase.plot(np.fft.fftshift(freq),
             np.fft.fftshift(np.angle(Y)),
             marker='.',
             label='Voie ' + str(idx_voie))
ax_phase.set(title='Phase de la T.F.D.')
ax_phase.legend()
ax_phase.grid(True)
ax_phase.set(xlabel='Fréquence (Hz)',ylabel='Phase (rd)')
phase_mouse =  lambda event: on_click_module(event, freq, mod_tf)
fig2.canvas.mpl_connect('button_press_event', phase_mouse)

print("moyenne :", np.mean(mod_tf[idx]))
base = np.polyval(p, freq_positive) - mod_tf[idx]
print("écart-type :", np.std(base))
plt.show()