# LyricAligner
Takes LRCLIB, Spotify, Musixmatch and NetEase lyrics, gets the current played song's mp3 file using yt-dlp, then runs it through a light speech recognition model.
In short, it takes the human precision for the words, and machine precision for timestamps.
Currently is set for English, Czech and Slovak, but that can be easily changed in code.
It is far from perfect, but for my use, it does a great job for not as popular songs that dont have as good lyrics as more popular ones.
^Refines paragraph lyrics into much cleaner and easier to track lyrics.
This is a spicetify plugin based on [The standalone popup lyrics](https://github.com/spicetify/cli/blob/main/Extensions/popupLyrics.js) (the standalone version is great, much love to the person who made it!!)


#  1.) Prerequisites 

Make sure you have the following installed on your system:
- **[Spicetify](https://spicetify.app/)**
- **Python 3.9+** (Make sure to check *"Add Python to PATH"* during installation)
- **FFmpeg** (Required for audio processing):
  - **Windows:** Run `winget install Gyan.FFmpeg` in PowerShell, or download from [ffmpeg.org](https://ffmpeg.org).
  - **macOS:** `brew install ffmpeg`
  - **Linux:** `sudo apt install ffmpeg`

#  2.) Installing the backend server 

1. **Clone or download this repository:**
   ```bash
   git clone https://github.com/your-username/LyricAligner.git
   cd LyricAligner
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Or just double-click `run.bat` if you are on Windows).*

3. **Start the alignment server:**
   ```bash
   python align_server.py
   ```

*On the very first run, it will download OpenAI's `base` Whisper model (~140 MB). Once you see `Model ready! Listening on port 8080...`, leave this terminal open in the background.*

---

#  3. Installing the Spicetify Extension 

1. **Locate your Spicetify `Extensions` folder:**
   - **Windows:** Run `explorer (spicetify path extensions)` in PowerShell, or navigate to `%userprofile%\.spicetify\Extensions`
   - **macOS / Linux:** `~/.config/spicetify/Extensions`

2. **Replace `popupLyrics.js`:**
   Copy the modified `popupLyrics.js` from this repo and place it inside your `Extensions` folder (overwrite the existing file).

3. **Apply Spicetify changes:**
   Open your terminal and run:
   ```bash
   spicetify apply
   ```

---

#  4. How to Use 

1. Open Spotify and start playing a song.
2. Click the **Popup Lyrics** icon in the top navigation bar to open the lyric window.
3. If the song has chunky, paragraph-style lyrics:
   - The original lyrics will show up immediately so you don't have to wait.
   - Look at your Python terminal: you will see it download the audio, run forced alignment, and cache the result.
   - Within a few seconds, the floating lyrics will **seamlessly hot-swap** into clean, line-by-line synced lyrics!
4. **Next time you play that song:** It loads instantly from the local `./lyrics_cache/` folder without needing to download or process anything again.


  

 🙏 Credits & Acknowledgments
**[khanhas](https://github.com/khanhas)** for creating Spicetify and the original `popupLyrics` extension.
**[mantou132](https://github.com/mantou132/Spotify-Lyrics)** for the original lyric rendering UI foundation.
**[kyrie25](https://github.com/kyrie25)** and the **[Spicetify Team](https://github.com/spicetify)** for maintaining the Spicetify ecosystem.
**[jianfch](https://github.com/jianfch/stable-ts)** for `stable-ts` (Whisper forced alignment).
**[yt-dlp](https://github.com/yt-dlp/yt-dlp)** for audio streaming extraction.
