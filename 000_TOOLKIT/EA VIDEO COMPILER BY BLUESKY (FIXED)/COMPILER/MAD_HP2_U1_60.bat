@echo off
setlocal enabledelayedexpansion

:: Make the workload.
if not exist ".\temp" mkdir "temp"
if not exist ".\temp\avi" mkdir "temp\avi"
if not exist ".\temp\avi\avi_vp6" mkdir "temp\avi\avi_vp6"
if not exist ".\temp\avi\avi_mpeg4" mkdir "temp\avi\avi_mpeg4"
if not exist ".\temp\Wav" mkdir "temp\Wav"
if not exist ".\temp\Final" mkdir "temp\Final"
if not exist ".\temp\Final" mkdir "Release"
for %%f in (MP4\*.mp4) do (mkdir "temp\Final\%%~nf")

@echo off
for %%f in (mp4\*.mp4) do (
    set "filename=%%~nf"
    tools\FFMPEG\ffmpeg -i "%%f" -c:v libxvid -r 60 -b:v 15M -an ".\temp\avi\avi_mpeg4\!filename!.avi"
)

:: rem Convert MP4 to WAV using ffmpeg
for %%f in (mp4\*.mp4) do (
    set "filename=%%~nf"
    tools\FFMPEG\ffmpeg -i "%%f" -acodec pcm_s16le -ar 44100 -ac 2 ".\temp\Wav\!filename!.wav"
)


for %%f in (MP4\*.mp4) do (mkdir "temp\Final\%%~nf")

:: rem Convert WAV to ASF using sx_2004
for %%f in (temp\WAV\*.wav) do (
  tools\sx\sx -sndstream -eaxa_blk -fps29.971 "temp\WAV\%%~nf.wav" -= ".\temp\final\%%~nf\%%~nf.asf"
)

:: Convert AVI to VP6 using your specified command
for %%f in (temp\avi\avi_mpeg4\*.avi) do (
    set "filename=%%~nf"
    tools\VP6\gx -mad -fps60 -v4 -high "%%f"="temp\final\%%~nf\!filename!.mad"
)

for %%f in (mp4\*.mp4) do (
    set "filename=%%~nf"
    tools\quickbms\quickbms.exe -Y tools\quickbms\Mad_muxer.bms .\temp\final\!filename!\ .\release
)

:: rem Remove .asf from filenames
for %%f in (Release\*.mad) do (
    set "filename=%%~nf"
    set "newfilename=!filename:.ASF.mad=!"
    ren "%%f" "!newfilename!.mad"
)

:: rem Remove .ASF from filenames
for %%f in (Release\*.ASF*) do (
    set "filename=%%~nf"
    set "extension=%%~xf"
    set "newfilename=!filename:.ASF=!%%~xf"
    ren "%%f" "!newfilename!"
)

:: Deletes temp when compile is done.
rmdir /s /q temp

endlocal


