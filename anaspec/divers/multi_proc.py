import threading
import timeit
import numpy as np
import scipy.signal


import multiprocessing

def f(x):
    return x*x

class Calcul_fft(threading.Thread):
    def __init__(self, x):
        threading.Thread.__init__(self)
        self.x = x
    
    def run(self):
        self.z = scipy.fft.fft(self.x)


if __name__ == '__main__':
    rng = np.random.default_rng(12345)
    cpu_time=[]
    n = 2 ** 25
    x = np.random.random_sample(size=(n, 16))-0.5
    t_deb = timeit.default_timer()
    th = []
    for idx in range(x.shape[1]):
        th.append(Calcul_fft(x[:,idx]))
    for idx in range(x.shape[1]):
        th[idx].start()
    for idx in range(x.shape[1]):
        th[idx].join()
    t_fin = timeit.default_timer()
    print( t_fin - t_deb)
    for t in th:
        print(t.z.shape, t.z[10])
    t_deb = timeit.default_timer()
    for idx in range(x.shape[1]):
        z = scipy.fft.fft(x[:,idx])
    t_fin = timeit.default_timer()
    print( t_fin - t_deb)