import pytesseract
from PIL import ImageGrab, Image
import edge_tts
import keyboard
import asyncio
import pygame
import datetime
import os
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

async def speak_text(text, voice):
    enforce_file_limit(".", ".mp3")
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + f"{int(datetime.datetime.now().microsecond / 10000):02d}"
    filename = f"tts_output_{timestamp}.mp3"
    await edge_tts.Communicate(text, voice).save(filename)
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

def capture_and_speak(region, voice):
    text = capture_text(region)
    if text: asyncio.run(speak_text(text, voice))

region = (0, 900, 1920, 1080)
female_voice, male_voice = "en-US-AriaNeural", "en-US-ChristopherNeural"

print("Press 'Up Arrow' for female voice and 'Down Arrow' for male voice.")
while True:
    if keyboard.is_pressed('up'):
        capture_and_speak(region, female_voice)
        time.sleep(0.2)
    elif keyboard.is_pressed('down'):
        capture_and_speak(region, male_voice)
        time.sleep(0.2)
    time.sleep(0.1)
