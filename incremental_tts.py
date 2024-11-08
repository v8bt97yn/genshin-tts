import pytesseract
from PIL import ImageGrab, Image
import edge_tts
import logging
import keyboard
import asyncio
import pygame
import datetime
import os
import time

# Initialize
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
pygame.mixer.init()
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
os.makedirs("captured_images", exist_ok=True)

# Limit the number of files in a directory
def enforce_file_limit(directory, extension, limit=3):
    files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(extension)]
    if len(files) > limit:
        files.sort(key=os.path.getctime)  # Sort by creation time (oldest first)
        for file in files[:-limit]:       # Remove oldest files until limit is met
            os.remove(file)

# Capture and filter image for OCR
def capture_text(region):
    enforce_file_limit("captured_images", ".png")  # Ensure no more than 3 PNG files
    try:
        screenshot = ImageGrab.grab(bbox=region)
        filtered_image = exact_color_filter(screenshot, target_color=(245, 241, 237), tolerance=0)
        filtered_image.save("captured_images/sample_filtered.png")
        text = pytesseract.image_to_string(filtered_image, config='--psm 6').replace("\n", " ").strip()
        logging.debug(f"Filtered text: '{text}'")
        return text
    except Exception as e:
        logging.error(f"Error in capture or OCR: {e}")
        return ""

# Color filter to retain specific colors
def exact_color_filter(image, target_color, tolerance=15):
    data = [(0, 0, 0) if all(abs(item[i] - target_color[i]) <= tolerance for i in range(3)) else (255, 255, 255) 
            for item in image.convert('RGB').getdata()]
    new_image = Image.new('RGB', image.size)
    new_image.putdata(data)
    return new_image

# Speak text with TTS using the specified voice
async def speak_text(text, voice):
    enforce_file_limit(".", ".mp3")  # Ensure no more than 3 MP3 files
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + f"{int(datetime.datetime.now().microsecond / 10000):02d}"
    filename = f"tts_output_{timestamp}.mp3"
    await edge_tts.Communicate(text, voice).save(filename)
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

# Main function to capture and speak text with selected voice
def capture_and_speak(region, voice):
    logging.info("Starting text capture and TTS.")
    text = capture_text(region)
    if text:
        logging.info(f"Speaking: {text}")
        asyncio.run(speak_text(text, voice))
    else:
        logging.debug("No text captured to speak.")
    logging.info("Finished capture and speak function.")

# Set region and capture on key press
region = (0, 900, 1920, 1080)
female_voice = "en-US-AriaNeural"  # Female voice
male_voice = "en-US-ChristopherNeural"      # Male voice

print("Press 'Up Arrow' for female voice and 'Down Arrow' for male voice.")
while True:
    if keyboard.is_pressed('up'):
        capture_and_speak(region, female_voice)
        time.sleep(0.2)  # Debounce delay
    elif keyboard.is_pressed('down'):
        capture_and_speak(region, male_voice)
        time.sleep(0.2)  # Debounce delay
    time.sleep(0.1)
