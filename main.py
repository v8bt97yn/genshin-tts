import os
import time
import mss
import keyboard
import pygame
import pytesseract
import asyncio
import edge_tts
from datetime import datetime
from PIL import Image

pygame.mixer.init()
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

AUDIO_DIR = "cache/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

with mss.mss() as sct:
    mon = sct.monitors[1]
REGION = (
    int(mon["width"] * 0.1),
    int(mon["height"] * 0.75),
    int(mon["width"] * 0.9),
    int(mon["height"] * 0.94),
)

VOICE_SETTINGS = {
    "female": ("en-US-JennyNeural", "+0Hz"),
    "male":   ("en-US-ChristopherNeural", "+0Hz"),
}

MAX_FILES = 1
TTS_RATE = "+40%"

def enforce_file_limit(directory, extension, limit):
    """Remove oldest files in `directory` if they exceed `limit`."""
    files = sorted(
        [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(extension)],
        key=os.path.getctime
    )
    for f in files[:-limit]:
        os.remove(f)

def apply_color_filter(image, target_color=(246, 242, 238), tol=5):
    """Convert pixels near `target_color` to black, others to white."""
    data = [
        (0, 0, 0) if all(abs(ch - tc) <= tol for ch, tc in zip(pixel, target_color))
        else (255, 255, 255)
        for pixel in image.convert("RGB").getdata()
    ]
    filtered = Image.new("RGB", image.size)
    filtered.putdata(data)
    return filtered

def capture_text(region):
    """Capture specified region, apply filter, run OCR, and return processed text."""
    with mss.mss() as sct:
        shot = sct.grab({
            "left": region[0],
            "top": region[1],
            "width": region[2] - region[0],
            "height": region[3] - region[1]
        })
    img = Image.frombytes("RGB", shot.size, shot.rgb)
    filtered_img = apply_color_filter(img)
    text = pytesseract.image_to_string(filtered_img, config='--oem 3 --psm 6')
    return text.replace("\n", " ").strip()

# -- Asynchronous Text-to-Speech using python-edge-tts --
async def _speak_async(text, voice, pitch, audio_path):
    """Async TTS function: uses python-edge-tts to generate audio file."""
    communicator = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=TTS_RATE,
        pitch=pitch
    )
    await communicator.save(audio_path)

def speak_text_fixed(text, voice, pitch):
    """Synchronous wrapper that calls our async TTS function and plays audio."""
    if not text:
        return

    enforce_file_limit(AUDIO_DIR, ".mp3", MAX_FILES)
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    audio_path = os.path.join(AUDIO_DIR, f"tts_{ts}.mp3")

    try:
        # Run the async TTS function in a synchronous context
        asyncio.run(_speak_async(text, voice, pitch, audio_path))
        print(f"Saved audio at: {audio_path}")
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()
    except Exception as e:
        print(f"TTS error: {e}")

def main():
    print("Press '.' (female) or ',' (male) to speak text.")
    while True:
        if keyboard.is_pressed('.'):
            speak_text_fixed(capture_text(REGION), *VOICE_SETTINGS["female"])
        elif keyboard.is_pressed(','):
            speak_text_fixed(capture_text(REGION), *VOICE_SETTINGS["male"])
        time.sleep(0.1)

if __name__ == "__main__":
    main()
