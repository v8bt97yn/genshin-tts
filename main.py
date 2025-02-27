import os, time, asyncio, datetime
import mss, keyboard, pygame, pytesseract, edge_tts
from PIL import Image

# Initialize modules and directories
pygame.mixer.init()
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
AUDIO_DIR = "cache/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

# Global mss instance reused for screen capture
sct = mss.mss()
mon = sct.monitors[1]
REGION = (int(mon["width"] * 0.1), int(mon["height"] * 0.75),
          int(mon["width"] * 0.9), int(mon["height"] * 0.94))

VOICE_SETTINGS = {"female": ("en-US-JennyNeural", "+0Hz"),
                  "male": ("en-US-ChristopherNeural", "+0Hz")}
MAX_FILES, TTS_RATE = 1, "+40%"

# Target color #f2f6ee => RGB (242, 246, 238) with tolerance reduced to 7
TARGET_COLOR = (242, 246, 238)
COLOR_TOLERANCE = 7
POLL_INTERVAL = 0.1  # seconds

def enforce_file_limit(directory, ext, limit):
    files = sorted([os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(ext)],
                   key=os.path.getctime)
    for f in files[:-limit]:
        os.remove(f)

def capture_region(region):
    shot = sct.grab({"left": region[0], "top": region[1],
                     "width": region[2] - region[0], "height": region[3] - region[1]})
    return Image.frombytes("RGB", shot.size, shot.rgb)

def count_color_pixels(img, target=TARGET_COLOR, tol=COLOR_TOLERANCE):
    # Since img is already in RGB mode, no need to convert
    return sum(1 for pixel in img.getdata() if all(abs(ch - tc) <= tol for ch, tc in zip(pixel, target)))

def apply_color_filter(img, target=TARGET_COLOR, tol=COLOR_TOLERANCE):
    # Map target-colored pixels to black, all others to white.
    data = [(0, 0, 0) if all(abs(ch - tc) <= tol for ch, tc in zip(pixel, target))
            else (255, 255, 255) for pixel in img.getdata()]
    filtered = Image.new("RGB", img.size)
    filtered.putdata(data)
    return filtered

def capture_text(img):
    filtered_img = apply_color_filter(img)
    return pytesseract.image_to_string(filtered_img, config='--oem 3 --psm 6').replace("\n", " ").strip()

async def _speak_async(text, voice, pitch, audio_path):
    await edge_tts.Communicate(text=text, voice=voice, rate=TTS_RATE, pitch=pitch).save(audio_path)

def speak_text_fixed(text, voice, pitch):
    if not text:
        return
    enforce_file_limit(AUDIO_DIR, ".mp3", MAX_FILES)
    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    audio_path = os.path.join(AUDIO_DIR, f"tts_{ts}.mp3")
    try:
        asyncio.run(_speak_async(text, voice, pitch, audio_path))
        print(f"Saved audio at: {audio_path}")
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()
    except Exception as e:
        print(f"TTS error: {e}")

def wait_for_stable_pixels(region):
    img_prev = capture_region(region)
    count_prev = count_color_pixels(img_prev)
    while True:
        time.sleep(POLL_INTERVAL)
        img_new = capture_region(region)
        count_new = count_color_pixels(img_new)
        delta = count_new - count_prev
        if delta > 100:
            print(f"Large jump detected ({delta}); resetting measurement.")
            img_prev, count_prev = img_new, count_new
            continue
        if delta > 50:
            print(f"Increase of {delta} detected; waiting for stabilization.")
            img_prev, count_prev = img_new, count_new
        else:
            print(f"Stable detected with delta {delta}. Proceeding.")
            return img_new

def main():
    print("Press '.' (female) or ',' (male) to speak text.")
    while True:
        key = None
        if keyboard.is_pressed('.'):
            key = '.'
        elif keyboard.is_pressed(','):
            key = ','
        
        if key:
            stable_img = wait_for_stable_pixels(REGION)
            text = capture_text(stable_img)
            if key == '.':
                speak_text_fixed(text, *VOICE_SETTINGS["female"])
            else:
                speak_text_fixed(text, *VOICE_SETTINGS["male"])
            time.sleep(0.5)
        time.sleep(0.1)

if __name__ == "__main__":
    main()
