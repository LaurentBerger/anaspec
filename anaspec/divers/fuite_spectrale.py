import numpy as np
import soundfile as sf
import sounddevice as sd
from matplotlib import pyplot as plt

Fe = 22050
N = 16384*128
te = np.arange(0,N)/Fe
freq = np.fft.fftfreq(N)*Fe
val_f0 = np.arange(10,20,2)*Fe/N
t_deb = np.random.randint(0,max(te)/4)
D = np.random.randint(max(te)/8,max(te)/4)
D = N /(int(N / (Fe*D))*Fe)
t_fin = t_deb + D
a0 = 1 + np.random.randint(0,2)
f0 =  np.random.randint(400,600)
f0 = int(f0* N/Fe) * Fe/N
l_ratio = [*range(0,6,1)]
nb_courbe = len(l_ratio)
fig1, ax1 = plt.subplots(nrows=nb_courbe, ncols=1)
for idx, fratio in enumerate(l_ratio):
    y = a0 * np.sin(2*np.pi*te*(f0+fratio/10*Fe/N)) 
    y[te<t_deb] = 0
    y[te>t_fin] = 0
    nom_fichier_son = 'Signal temporel'
    print("Nombre d'échantillons : ", N)
    print("Fréquence d'échantillonnage : ", Fe)
    S = np.fft.fft(y)
    # Tracer du signal temporel
    Y = S
    ax1[idx].plot(np.fft.fftshift(freq),
             np.fft.fftshift(np.abs(Y).real/Fe),
             label='Signal ')
    ax1[idx].set(title='Module de la T.F.D.')
    ax1[idx].set_xlim(f0 - 5/D , f0 + 5/D)
    ax1[idx].legend() 
    ax1[idx].grid(True)
    ax1[idx].grid(True, which='minor', color='r', linestyle='-', alpha=0.2)
    ax1[idx].minorticks_on()
    ax1[idx].set_xlabel('Fréquence (Hz)')
    ax1[idx].set_ylabel('Amplitude (u.a.)')
    plt.pause(0.1)
plt.show()    