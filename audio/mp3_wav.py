import os
import time
import wx
try: 
    import ffmpeg
except:
    wx.MessageBox("ffmpeg-python  not installed ", wx.ICON_ERROR)
    

def wav_mp3_wav(evt, main_window=None):
    # check if ffmpeg is available on windows
    if os.path.splitdrive(os.getcwd())[0] != '':
        if os.path.exists("c:/temp/ffmpeg/bin"):
            os.environ["PATH"] = "c:/temp/ffmpeg/bin" + os.pathsep + os.environ["PATH"]
        else:
            wx.LogWarning("ffmpeg not found in c:/temp/ffmpeg/bin\nffmpeg must be in system path")
    wx.LogMessage("Convert a wav file to mp3 (8, 32, 128, 320kbps) and mp3 to wav")
    # https://kkroening.github.io/ffmpeg-python/
    nom_fichier_ref = wx.FileSelector("Select wav file to convert",wildcard="*.wav")
    if nom_fichier_ref.strip():
        audio_wav = ffmpeg.input(nom_fichier_ref)
        bit_rate = ['8k', '32k', '128k', '320k']
        dlg = wx.ProgressDialog("Convert a wav file to mp3 (8, 32, 128, 320kbps) and mp3 to wav",
                                "",
                                maximum = 8,
                                parent=None,
                                style = wx.PD_APP_MODAL
                                )     
        idx = 0
        for ab in bit_rate: 
            nom_fichier = nom_fichier_ref + "_" + ab + ".mp3"
            dossier, fichier = os.path.split(nom_fichier)
            dlg.Update(idx, "Writing in " + dossier + "\n"+ fichier)
            cmd = audio_wav.output(nom_fichier,audio_bitrate=ab).overwrite_output()
            ffmpeg.compile(cmd)
            cmd.run_async(quiet=True)
            time.sleep(2)
            idx = idx + 1
            if not os.path.isfile(nom_fichier):
                dlg.Destroy()
                wx.MessageBox("Cannot convert " + nom_fichier_ref + "to mp3", "Error\Check ffmpeg install", wx.ICON_ERROR)
                if main_window:
                    main_window.SetFocus()
                return

        bit_rate = ['8k', '32k', '128k', '320k']
        for ab in bit_rate: 
            nom_fichier = nom_fichier_ref + "_" + ab + ".mp3"
            audio_mp3 = ffmpeg.input(nom_fichier)
            nom_fichier = nom_fichier_ref + "_" + ab + ".wav"
            dossier, fichier = os.path.split(nom_fichier)
            dlg.Update(idx, "Writing in " + dossier + "\n"+ fichier)
            cmd = audio_mp3.output(nom_fichier,ar=44100).overwrite_output()
            ffmpeg.compile(cmd)
            cmd.run_async(quiet=True)
            time.sleep(2)
            if not os.path.isfile(nom_fichier):
                dlg.Destroy()
                wx.MessageBox("Cannot convert " + nom_fichier + "to wav", "Error", wx.ICON_ERROR)
                if main_window:
                    main_window.SetFocus()
                return
            idx = idx + 1
        dlg.Destroy()
        if main_window:
            main_window.SetFocus()
