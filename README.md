# anaspec
Spectrum Analyzer using python (>= 3.10)
using wxPython numpy scipy soundfile sounddevice matplolib

To run program click run.py
You can select a desired device using  "input device" menu
Then you select sampling frequency available with this device.
 
![alt text](https://github.com/LaurentBerger/anaspec/blob/master/images/interface.jpg)

Press button to start sampling. Signal is plotted in  Oscilloscope window (time signal Tab). Only index ranging ranging from beginning to end indices are plotted. Values can be changed during sampling with slider.

![alt text](https://github.com/LaurentBerger/anaspec/blob/master/images/time_signal.jpg)

Spectrum  is plotted in  Oscilloscope window (Spectral Tab). It can be real time spectrum if button Enable plot spectrum is red (in Interface window spectrum tab). Frequency plotted can be select using slider in Interface window spectrum tab

![alt text](https://github.com/LaurentBerger/anaspec/blob/master/images/interface_spectrum.jpg)
