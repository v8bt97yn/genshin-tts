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
os.makedirs("captured_images", exist_ok=True)

# Configuration
REGION = (250, 890, 1670, 1050)  # Updated screen capture region
VOICE_SETTINGS = {
    '1': ("en-US-ChristopherNeural", "-5Hz"),  # Male voice, lower pitch
    '4': ("en-US-ChristopherNeural", "+5Hz"),  # Male voice, higher pitch
    '7': ("en-US-ChristopherNeural", "+15Hz"), # Male voice, highest pitch
    '3': ("en-US-AriaNeural", "-5Hz"),        # Female voice, lower pitch
    '6': ("en-US-AriaNeural", "+5Hz"),        # Female voice, higher pitch
    '9': ("en-US-AriaNeural", "+15Hz"),       # Female voice, highest pitch
}
MAX_FILES = 3  # Maximum number of stored audio/image files for cleanup

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
    enforce_file_limit("captured_images", ".png", MAX_FILES)
    screenshot = ImageGrab.grab(bbox=region)
    filtered_image = apply_color_filter(screenshot, (245, 241, 237), 15)
    filtered_image.save("captured_images/sample_filtered.png")
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
    enforce_file_limit(".", ".mp3", MAX_FILES)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"tts_output_{timestamp}.mp3"

    # Debug: Print raw text
    print("Raw Text to TTS:", text)

    # Directly build the edge-tts command without extra escaping
    command = [
        "edge-tts",
        f"--voice={voice}",
        f"--pitch={pitch}",
        f"--text={text}",  # Pass text as-is
        f"--write-media={filename}"
    ]

    try:
        # Execute the edge-tts command
        subprocess.run(command, check=True)

        # Debug: Confirm audio file generation
        print(f"Audio file generated: {filename}")

        # Play the audio file using pygame
        pygame.mixer.music.load(filename)
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
    print("Press numpad keys 1-4 (male voice) or 6-9 (female voice) to trigger TTS.")
    print("Key 5 is inactive.")
    while True:
        for key, (voice, pitch) in VOICE_SETTINGS.items():
            if keyboard.is_pressed(key):
                capture_and_speak(REGION, voice, pitch)
                time.sleep(0.2)  # Debounce to avoid multiple triggers
        time.sleep(0.1)

if __name__ == "__main__":
    main()
