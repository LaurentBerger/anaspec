# anaspec
Spectrum Analyzer in python (>= 3.10)
using wxPython numpy scipy soundfile sounddevice matplolib
![alt text](https://github.com/LaurentBerger/anaspec/blob/master/anaspec.jpg)

To run program click run.py
You can select a desired device using  "input device" menu
Then you select sampling frequency available with this device.
 
![alt text](https://github.com/LaurentBerger/anaspec/blob/master/images/interface.jpg)

Press button to start sampling. Signal is plotted in  Oscilloscope window (time signal Tab). Only index ranging ranging from beginning to end indices are plotted. Values can be changed during sampling with slider.

![alt text](https://github.com/LaurentBerger/anaspec/blob/master/images/time_signal.jpg)

Spectrum  is plotted in  Oscilloscope window (Spectral Tab). It can be real time spectrum if button Enable plot spectrum is red (in Interface window spectrum tab). Frequency plotted can be select using slider in Interface window spectrum tab

![alt text](https://github.com/LaurentBerger/anaspec/blob/master/images/interface_spectrum.jpg)


click and press shift key in spectral tab : give frequency and fft modulus
click and press ctrl key in spectral tab : plot a cross around peak more than -x dB than clicked value 
click and press alt key in spectral tab : plot bandwidth at level -x dB relative to clicked value 
click and press ctrl+shift key in spectral tab : total harmonic distorsion
All numerical values are printed in window named Oscilloscope Logger and in grid Marker values (copy and paste values in your favorite spreadsheet is available) 

You can fix space between peak in parameters (intervace window) tab using slider
You can change level of bandpass in parameters (intervace window) tab using slider Bandwidth