import pytesseract
from PIL import ImageGrab, Image
import keyboard
import pygame
import datetime
import os
import subprocess
import time

# Initialize pygame and pytesseract
pygame.mixer.init()
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Create cache directories
os.makedirs("cache/image", exist_ok=True)
os.makedirs("cache/audio", exist_ok=True)

# Configuration
REGION = (250, 840, 1670, 1020)  # Updated screen capture region
VOICE_SETTINGS = {
    ('up', 'right'): ("en-US-JennyNeural", "+15Hz"),  # Female voice, higher pitch
    ('up', 'left'): ("en-US-SteffanNeural", "+15Hz"),  # Male voice, higher pitch
    ('down', 'right'): ("en-US-MichelleNeural", "-15Hz"),  # Female voice, lower pitch
    ('down', 'left'): ("en-US-ChristopherNeural", "-15Hz"),  # Male voice, lower pitch
}
MAX_AUDIO_FILES = 2  # Maximum number of stored audio files

# Utility: Limit stored files in a directory
def enforce_file_limit(directory, extension, limit):
    files = sorted(
        [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(extension)],
        key=os.path.getctime
    )
    for file in files[:-limit]:
        os.remove(file)

# Capture screen text
def capture_text(region):
    """Capture text from the specified screen region and remove line breaks."""
    enforce_file_limit("cache/image", ".png", MAX_AUDIO_FILES)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    image_path = f"cache/image/screenshot_{timestamp}.png"
    filtered_image_path = f"cache/image/sample_filtered_{timestamp}.png"

    screenshot = ImageGrab.grab(bbox=region)
    filtered_image = apply_color_filter(screenshot, (246, 242, 238, 255), 5)
    filtered_image.save(filtered_image_path)
    raw_text = pytesseract.image_to_string(filtered_image, config='--oem 3 --psm 6')
    # Replace line breaks with a single space
    processed_text = raw_text.replace("\n", " ").strip()
    return processed_text

# Apply color filter to improve OCR
def apply_color_filter(image, target_color, tolerance):
    """Convert non-target colors to white and target colors to black."""
    data = [
        (0, 0, 0) if all(abs(channel - target_color[i]) <= tolerance for i, channel in enumerate(pixel)) else (255, 255, 255)
        for pixel in image.convert('RGB').getdata()
    ]
    new_image = Image.new('RGB', image.size)
    new_image.putdata(data)
    return new_image

# Text-to-Speech with Punctuation Preservation
def speak_text_fixed(text, voice, pitch):
    """Convert text to speech using edge-tts, preserving punctuation."""
    enforce_file_limit("cache/audio", ".mp3", MAX_AUDIO_FILES)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    audio_path = f"cache/audio/tts_output_{timestamp}.mp3"

    # Debug: Print raw text
    print("Raw Text to TTS:", text)

    # Directly build the edge-tts command without extra escaping
    command = [
        "edge-tts",
        f"--voice={voice}",
        f"--pitch={pitch}",
        f"--text={text}",  # Pass text as-is
        f"--write-media={audio_path}"
    ]

    try:
        # Execute the edge-tts command
        subprocess.run(command, check=True)

        # Debug: Confirm audio file generation
        print(f"Audio file generated: {audio_path}")

        # Play the audio file using pygame
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()
    except subprocess.CalledProcessError as e:
        print(f"Error during TTS execution: {e}")

# Core functionality
def capture_and_speak(region, voice, pitch):
    """Capture text from screen and speak it."""
    text = capture_text(region)
    if text:
        print(f"Captured Text (Processed): {text}")  # Debugging output
        speak_text_fixed(text, voice, pitch)

# Main loop
def main():
    print("Use Up/Down as pitch modifiers and Left/Right for gender. Combine them to trigger TTS.")
    while True:
        # Detect modifier keys
        up_pressed = keyboard.is_pressed('up')
        down_pressed = keyboard.is_pressed('down')
        left_pressed = keyboard.is_pressed('left')
        right_pressed = keyboard.is_pressed('right')

        # Check for key combinations
        if up_pressed and left_pressed:
            capture_and_speak(REGION, *VOICE_SETTINGS[('up', 'left')])
        elif up_pressed and right_pressed:
            capture_and_speak(REGION, *VOICE_SETTINGS[('up', 'right')])
        elif down_pressed and left_pressed:
            capture_and_speak(REGION, *VOICE_SETTINGS[('down', 'left')])
        elif down_pressed and right_pressed:
            capture_and_speak(REGION, *VOICE_SETTINGS[('down', 'right')])
        
        time.sleep(0.1)  # Prevent excessive CPU usage

if __name__ == "__main__":
    main()
