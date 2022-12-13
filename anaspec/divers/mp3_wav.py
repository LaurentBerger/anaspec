import os
import ffmpeg
import wx

# check if ffmpeg is available on windows https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-essentials.7z
if os.path.splitdrive(os.getcwd())[0] != '':
    if os.path.exists("c:/temp/ffmpeg/bin"):
        os.environ["PATH"] = "c:/temp/ffmpeg-git-essentials.7z/bin" + os.pathsep + os.environ["PATH"]
    else:
        wx.LogWarning("ffmpeg not found\nffmpeg must be in system path")
wx.LogMessage("Convert a wav file to mp3 (8, 32, 128, 320kbps) and mp3 to wav")
# https://kkroening.github.io/ffmpeg-python/
my_app = wx.App()
nom_fichier_ref = wx.FileSelector("Select wav file to convert",wildcard="*.wav")
del my_app
audio_wav = ffmpeg.input(nom_fichier_ref)
bit_rate = ['8k', '32k', '128k', '320k']
for ab in bit_rate: 
    nom_fichier = nom_fichier_ref + "_" + ab + ".mp3"
    print("Writing ", nom_fichier)
    cmd = audio_wav.output(nom_fichier,audio_bitrate=ab).overwrite_output()
    ffmpeg.compile(cmd)
    cmd.run_async(quiet=True)

bit_rate = ['8k', '32k', '128k', '320k']
for ab in bit_rate: 
    nom_fichier = nom_fichier_ref + "_" + ab + ".mp3"
    audio_mp3 = ffmpeg.input(nom_fichier)
    nom_fichier = nom_fichier_ref + "_" + ab + ".wav"
    print("Writing ", nom_fichier)
    cmd = audio_mp3.output(nom_fichier,ar=44100).overwrite_output()
    ffmpeg.compile(cmd)
    cmd.run_async(quiet=True)
