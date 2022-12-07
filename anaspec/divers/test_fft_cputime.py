import time
import timeit
import numpy as np
import scipy
import matplotlib.pyplot


rng = np.random.default_rng(12345)
cpu_time=[]
N_deb = 12
val_N = np.random.randint(2**14, 2**17, size=2000)
# val_N[0:4] = [2**14, 2**15, 2**16, 2**17]
for n in val_N:
    x = np.random.random_sample(size=(n))-0.5
    # deb = time.perf_counter()
    t_deb = timeit.default_timer()
    y = scipy.fft.fft(x)
    # t_fin = time.perf_counter()
    t_fin = timeit.default_timer()
    cpu_time.append(t_fin - t_deb)
for p in range(1, 101):
    print(p)
    for idx, n in enumerate(val_N):
        x = np.random.random_sample(size=(n))-0.5
        # deb = time.perf_counter()
        t_deb = timeit.default_timer()
        y = scipy.fft.fft(x)
        # t_fin = time.perf_counter()
        t_fin = timeit.default_timer()
        cpu_time[idx] = (p * cpu_time[idx] + (t_fin - t_deb))/(p+1)
    
fig, ax = matplotlib.pyplot.subplots(nrows=1, ncols=1)
ax.scatter(val_N, cpu_time)
matplotlib.pyplot.show()
cpu =  np.array(cpu_time)
val_n= np.array(val_N)

val_N_p = [v for v in val_n if v % 8 ==0 ]
cpu_p = [t for v,t in zip(val_n, cpu) if v % 8 == 0 ]
val_N_i = [v for v in val_n if v % 8 != 0 ]
cpu_i = [t for v,t in zip(val_n, cpu) if v % 8 != 0 ]
d0 = [0.0418/130700, 0]
d1 = [0.0123/130700, 0]
y_0 = np.abs(np.polyval(d0, val_n)-cpu)
y_1 = np.abs(np.polyval(d1, val_n)-cpu)
y_d = np.array([y_0, y_1])
idx_d = y_d.argmin(axis=0)
idx_d0 = np.where(idx_d==0)
idx_d1 = np.where(idx_d==1)
fig, ax = matplotlib.pyplot.subplots(nrows=1, ncols=1)
ax.scatter(val_n[idx_d0[0]], cpu[idx_d0[0]], color='red')
ax.scatter(val_n[idx_d1[0]], cpu[idx_d1[0]], color='blue')
ax.plot(val_n, np.polyval(d0, val_n), color='red')
ax.plot(val_n, np.polyval(d1, val_n), color='blue')
matplotlib.pyplot.show()

