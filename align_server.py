# im genuinely not going to compile this because the filesize would be like 2gb

import os
import re
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import yt_dlp
import stable_whisper

PORT = 8080
CACHE_DIR = "./lyrics_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

print("Loading Whisper model...")
model = stable_whisper.load_model("base")
print("Model ready! Listening on port 8080...")

# tracks current song
current_active_song = None

def detect_lyrics_language(text):
    text_lower = text.lower()
    slovak_markers = ['ä', 'ô', 'ľ', 'ŕ', 'ĺ', 'dz', 'dž', 'nie je', 'veď', 'chceš', 'som', 'sme', 'ako']
    czech_markers = ['ř', 'ě', 'ů', 'jsem', 'jsou', 'proč', 'však', 'nebo', 'byl', 'pivo']

    slovak_score = sum(text_lower.count(m) for m in slovak_markers)
    czech_score = sum(text_lower.count(m) for m in czech_markers)

    if slovak_score > 0 or czech_score > 0:
        return "sk" if slovak_score >= czech_score else "cs"
    return "en"

def clean_search_title(title, artist):
    t = re.sub(r'\(.*?\)|\[.*?\]', '', title)
    t = re.sub(r'-\s*(remaster|bonus|live|edit).*', '', t, flags=re.IGNORECASE)
    return f"{artist} {t.strip()}"

def prepare_lyric_lines(raw_lines):
    CZ_SK_PREPOSITIONS = {'v', 'k', 's', 'z', 'o', 'u', 'a', 'i', 'do', 'na', 'od', 'po', 'ze', 've', 'ke', 'se'}
    final_lines = []

    for line in raw_lines:
        line = line.strip()
        if not line or line == "♪":
            continue

        sentence_parts = re.split(r'(?<=[.?!])\s+', line)
        for part in sentence_parts:
            part = part.strip()
            if not part:
                continue

            words = part.split()
            if len(words) > 10:
                mid = len(words) // 2
                if words[mid - 1].lower() in CZ_SK_PREPOSITIONS and mid > 1:
                    mid -= 1
                final_lines.append(" ".join(words[:mid]))
                final_lines.append(" ".join(words[mid:]))
            else:
                final_lines.append(part)

    return [l for l in final_lines if l.strip()]

def is_cache_valid(cached_lyrics):
    """Ensures cached data isn't corrupt or empty."""
    if not isinstance(cached_lyrics, list) or len(cached_lyrics) < 2:
        return False
    # Check that entries have valid times and non-blank text
    for item in cached_lyrics:
        if "text" not in item or "startTime" not in item:
            return False
        if not item["text"].strip():
            return False
    return True

def process_alignment(title, artist, raw_lines):
    global current_active_song
    song_id = f"{artist} - {title}"
    current_active_song = song_id

    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', f"{artist}_{title}")
    cache_path = os.path.join(CACHE_DIR, f"{safe_name}.json")

    # Check cache first
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
            if is_cache_valid(cached_data):
                print(f"[Aligner] Serving '{song_id}' from cache (Instant).")
                return cached_data
            else:
                print(f"[Aligner] Cache invalid for '{song_id}', re-aligning...")
        except Exception:
            pass

    print(f"\n[Aligner] Re-aligning lyrics for: {song_id}")
    lines_to_align = prepare_lyric_lines(raw_lines)
    if not lines_to_align:
        return None

    full_text = "\n".join(lines_to_align)
    audio_path = f"temp_{safe_name}.mp3"
    lang = detect_lyrics_language(full_text)

    # Abort check if the song got skipped
    if current_active_song != song_id:
        print(f"[Aligner] Canceled: '{song_id}' was skipped.")
        return None

    search_query = clean_search_title(title, artist)
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f"temp_{safe_name}",
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}],
        'quiet': True,
    }

    print(f"[Aligner] Downloading audio via: '{search_query}'...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"ytsearch1:{search_query} audio"])
    except Exception as e:
        print(f"[Aligner] Audio download error: {e}")
        return None

    # Abort check if the song got skipped during download
    if current_active_song != song_id:
        print(f"[Aligner] Canceled: '{song_id}' was skipped during download.")
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return None

    print(f"[Aligner] Running Whisper forced alignment ({lang})...")
    try:
        result = model.align(
            audio_path,
            full_text,
            language=lang,
          original_split=True,
          nonspeech_skip=2.0,
          max_word_dur=3.0
        )

        lyrics = []
        for segment in result.segments:
            text = segment.text.strip()
            if text:
                lyrics.append({
                    "text": text,
                    "startTime": round(segment.start, 2)
                })

        # Save song to cache for future requests
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(lyrics, f, ensure_ascii=False, indent=2)

        print(f"[Aligner] Done! Saved '{song_id}' to cache.")
        return lyrics
    except Exception as e:
        print(f"[Aligner] Alignment failed: {e}")
        return None
    finally:
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass

class LyricsHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/align":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            lyrics = process_alignment(data.get("title", ""), data.get("artist", ""), data.get("lines", []))
            if lyrics:
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"lyrics": lyrics}).encode("utf-8"))
                return

        self.send_response(400)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        return

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Allows handling requests and cancellations concurrently without freezing."""
    daemon_threads = True

if __name__ == "__main__":
    server = ThreadedHTTPServer(("localhost", PORT), LyricsHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()