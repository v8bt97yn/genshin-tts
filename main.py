import pytesseract
from PIL import ImageGrab, Image
import keyboard
import pygame
import datetime
import os
import subprocess
import shlex
import time

# Initialize
pygame.mixer.init()
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
os.makedirs("captured_images", exist_ok=True)

def enforce_file_limit(directory, extension, limit=3):
    files = sorted([os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(extension)], key=os.path.getctime)
    for file in files[:-limit]: os.remove(file)

def capture_text(region):
    enforce_file_limit("captured_images", ".png")
    screenshot = ImageGrab.grab(bbox=region)
    filtered_image = exact_color_filter(screenshot, (245, 241, 237), 5)
    filtered_image.save("captured_images/sample_filtered.png")
    return pytesseract.image_to_string(filtered_image, config='--psm 6').replace("\n", " ").strip()

def exact_color_filter(image, target_color, tolerance=15):
    data = [(0, 0, 0) if all(abs(item[i] - target_color[i]) <= tolerance for i in range(3)) else (255, 255, 255)
            for item in image.convert('RGB').getdata()]
    new_image = Image.new('RGB', image.size)
    new_image.putdata(data)
    return new_image

def speak_text_with_pitch(text, voice, pitch):
    enforce_file_limit(".", ".mp3")
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + f"{int(datetime.datetime.now().microsecond / 10000):02d}"
    filename = f"tts_output_{timestamp}.mp3"

    # Safely format the command arguments
    command = [
        "edge-tts",
        f"--voice={voice}",
        f"--pitch={pitch}",
        f"--text={shlex.quote(text)}",
        f"--write-media={filename}"
    ]

    # Run the CLI command
    try:
        subprocess.run(command, check=True)
        # Play the resulting audio
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
    except subprocess.CalledProcessError as e:
        print(f"Error executing edge-tts: {e}")
        print(f"Command: {' '.join(command)}")

def capture_and_speak(region, voice, pitch):
    text = capture_text(region)
    if text:
        speak_text_with_pitch(text, voice, pitch)

region = (0, 900, 1920, 1080)
male_voice, female_voice = "en-US-ChristopherNeural", "en-US-AriaNeural"
voice_settings = {
    '1': (male_voice, "-10Hz"),
    '4': (male_voice, "-5Hz"),
    '7': (male_voice, "-1Hz"),
    '3': (female_voice, "+1Hz"),
    '6': (female_voice, "+5Hz"),
    '9': (female_voice, "+10Hz"),
}

print("Press numpad 1-4 (male voice) or 6-9 (female voice) to trigger TTS. Key 5 is inactive.")
while True:
    for key, (voice, pitch) in voice_settings.items():
        if keyboard.is_pressed(key):
            capture_and_speak(region, voice, pitch)
            time.sleep(0.2)  # Debounce to avoid multiple triggers
    time.sleep(0.1)
