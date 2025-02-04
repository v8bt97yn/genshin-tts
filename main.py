import os, time, asyncio, threading, uuid, ctypes, datetime
import mss, keyboard, pygame, pytesseract, edge_tts, win32gui, win32con, win32process
from PIL import Image

pygame.mixer.init()
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
AUDIO_DIR = "cache/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

with mss.mss() as sct:
    mon = sct.monitors[1]
REGION = (int(mon["width"]*0.1), int(mon["height"]*0.75),
          int(mon["width"]*0.9), int(mon["height"]*0.94))
VOICE_SETTINGS = {"female": ("en-US-JennyNeural", "+0Hz"),
                  "male": ("en-US-ChristopherNeural", "+0Hz")}
MAX_FILES, TTS_RATE = 1, "+40%"
current_audio_id = None

def enforce_file_limit(d, ext, lim):
    files = sorted([os.path.join(d, f) for f in os.listdir(d) if f.endswith(ext)],
                   key=os.path.getctime)
    for f in files[:-lim]:
        os.remove(f)

def apply_color_filter(img, target=(246,242,238), tol=5):
    data = [(0,0,0) if all(abs(ch-tc) <= tol for ch, tc in zip(pixel, target))
            else (255,255,255) for pixel in img.convert("RGB").getdata()]
    filtered = Image.new("RGB", img.size)
    filtered.putdata(data)
    return filtered

def capture_text(r):
    with mss.mss() as sct:
        shot = sct.grab({"left": r[0], "top": r[1],
                         "width": r[2]-r[0], "height": r[3]-r[1]})
    img = Image.frombytes("RGB", shot.size, shot.rgb)
    return pytesseract.image_to_string(apply_color_filter(img),
                                       config='--oem 3 --psm 6').replace("\n", " ").strip()

async def _speak_async(text, voice, pitch, audio_path):
    await edge_tts.Communicate(text=text, voice=voice, rate=TTS_RATE, pitch=pitch).save(audio_path)

def switch_to_genshin_and_send_f():
    target = "Genshin Impact"
    hwnd = win32gui.FindWindow(None, target)
    if hwnd:
        if win32gui.IsIconic(hwnd): win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        fg = win32gui.GetForegroundWindow()
        fg_thread = win32process.GetWindowThreadProcessId(fg)[0] if fg else 0
        target_thread = win32process.GetWindowThreadProcessId(hwnd)[0]
        ctypes.windll.user32.AttachThreadInput(fg_thread, target_thread, True)
        win32gui.SetForegroundWindow(hwnd)
        win32gui.BringWindowToTop(hwnd)
        try:
            ctypes.windll.user32.SwitchToThisWindow(hwnd, True)
        except Exception:
            pass
        ctypes.windll.user32.AttachThreadInput(fg_thread, target_thread, False)
        time.sleep(0.3)
        keyboard.send("f")
        print("Switched to 'Genshin Impact' and sent 'f'.")
    else:
        print(f"Window '{target}' not found.")

def monitor_audio_finish(aid):
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    if aid == current_audio_id:
        print("Audio finished naturally. Triggering switch.")
        switch_to_genshin_and_send_f()
    else:
        print("Audio finished, but a newer TTS call was made.")

def speak_text_fixed(text, voice, pitch):
    global current_audio_id
    if not text: return
    enforce_file_limit(AUDIO_DIR, ".mp3", MAX_FILES)
    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    audio_path = os.path.join(AUDIO_DIR, f"tts_{ts}.mp3")
    try:
        asyncio.run(_speak_async(text, voice, pitch, audio_path))
        print(f"Saved audio at: {audio_path}")
        aid = str(uuid.uuid4())
        current_audio_id = aid
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()
        threading.Thread(target=monitor_audio_finish, args=(aid,), daemon=True).start()
    except Exception as e:
        print(f"TTS error: {e}")

def main():
    print("Press '.' (female) or ',' (male) to speak text.")
    while True:
        if keyboard.is_pressed('.'):
            speak_text_fixed(capture_text(REGION), *VOICE_SETTINGS["female"])
            time.sleep(0.5)
        elif keyboard.is_pressed(','):
            speak_text_fixed(capture_text(REGION), *VOICE_SETTINGS["male"])
            time.sleep(0.5)
        time.sleep(0.1)

if __name__ == "__main__":
    main()
