"""
Exemple de d'ajustement non linéaire
"""
import doctest
import numpy as np
import scipy.optimize 
import scipy.signal
import matplotlib.pyplot as plt
import soundfile as sf
import sounddevice as sd
import wx


def fct_trapeze(var_t, a=1, f0=0.2, bp=0.3,  df=0.01, b=0):
    """
    Fonction fct_trapeze dépendant de la variable var_t
    avec fct_trapeze(t) = parama_a quand param_f0<t<param_f1 et
    et décroissance linéaire vers 0
    Argument:
    var_t --> nombre
    a  --> amplitude rectangle
    f0 --> début du rectangle
    bp --> band passante chirp
    df --> largeur zone décroissante
    b  --> valeur bruit
    >>> fct_rect(0.05, 2, 0.1, 0.2, 0.01, 0.001)
    0.001
    >>> fct_rect(0.21, 2, 0.1, 0.2, 0.01, 0.001)
    2
    >>> fct_rect(0.41, 2, 0.1, 0.2, 0.01, 0.001)
    0.01
    """
    if isinstance(var_t, np.ndarray):
        df = 0.001
        f =  np.zeros(var_t.shape, np.float64)
        idx = np.logical_and(var_t>=f0, var_t<=f0+bp)
        f[idx] = a
        idx = np.logical_and(var_t>f0-df, var_t<f0)
        f[idx]= (var_t[idx] - f0 + df) * (a-b) / df
        idx = np.logical_and(var_t>f0+bp, var_t<f0+df+bp)
        f[idx]= (var_t[idx] - (f0+bp)) * (b-a) / df+ a
        f = np.clip(f,0,1)
        idx = np.logical_or(var_t<f0-df, var_t>f0+df+bp)
        f[idx] = b
        return f
    else:
        if f0<var_t<f1:
            return a
        else:
            return b 
    


doctest.testmod()
if __name__ == '__main__':
    my_app = wx.App()
    nom_fichier_son = wx.FileSelector("Fichier son",wildcard="*.wav")
    del my_app
    w , Fe = sf.read(nom_fichier_son)
    N = w.shape[0]
    legende =  nom_fichier_son.split('\\')[-1]
    f0 = float(input("Fréquence basse du chirp "))
    f1 = float(input("Fréquence haute du chirp "))
    te = np.arange(0,N)/Fe
    bp = f1 - f0
    w_chirp = scipy.signal.chirp(te, f0=f0, f1=f0+bp, t1=max(te), method='linear')
    w_mls = 
    print("Nombre d'échantillons : ", N)
    print("Fréquence d'échantillonnage : ", Fe)
    print("Nombre de voies : ", w.shape)
    if len(w.shape) == 2:
        w = w[:,0]
        print("Passage en mono du signal")

    W = np.fft.fft(w)
    freq = np.fft.fftfreq(N)*Fe
    fig1, ax1 = plt.subplots(nrows=1, ncols=1)
    freq =  np.fft.fftshift(freq)
    idx_sup = freq>0
    W_sup = np.fft.fftshift(np.abs(W).real/Fe)[idx_sup]
    freq_sup = freq[idx_sup]
    idx_bp = np.logical_and(freq_sup > f0, freq_sup < f1)
    moy_bp = np.mean(W_sup[idx_bp])
    std_bp = np.std(W_sup[idx_bp])
    ax1.plot(freq_sup, W_sup)
    
    ax1.set(title='Module de la T.F.D.')
    coeff, pcov = scipy.optimize .curve_fit(  # pylint: disable=unbalanced-tuple-unpacking
                            fct_trapeze,
                            freq_sup/Fe,
                            W_sup,
                            p0=[max(W_sup), 1500 / Fe, 2000/ Fe, 0.012, 0],
                            bounds=(0, 1),
                            maxfev=200000
                            )
    # affichage des paramètres
    print("Les paramètres de la fonction sont ", coeff)
    # calcule des ordonnées au point x de la fonction mon_modele_1
    y_est = fct_trapeze(freq_sup/Fe, *coeff)
    # calcul de l'erreur quadratique
    print("L'erreur quadratique est égal à :", np.mean((W_sup-y_est) ** 2))
    courbe2 = ax1.plot(freq_sup, y_est, color='blue', label='Fonction ajustée')
    ax1.vlines(coeff[1]*Fe,0,max(W_sup), colors='red', linestyles='dotted')
    ax1.vlines((coeff[1]+coeff[2])*Fe,0,max(W_sup), colors='red', linestyles='dotted')
    ax1.hlines(moy_bp,f0,f1, colors='red', linestyles='dotted')
    ax1.legend([legende,
                'Rect ' +str(int(coeff[1]*Fe)) + 'Hz//' + str(int((coeff[1]+coeff[2])*Fe)) +'Hz',
                'Moyenne sur BP avec écart type de ' + str(std_bp)])
    ax1.grid()
    plt.show()
