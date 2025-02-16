import logging
import requests
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO
import time


# Initialize RFID reader
reader = SimpleMFRC522()

# Moode REST API base URL
MOODE_API_BASE = "http://moode.local/command/?cmd="

# Map RFID card IDs to songs (update with your own mappings) TODO make this import from another file for easier trackiung
RFID_TO_SONG = {
    "12345890": "NAS/TRX-FLAC/YES/The Yes Album/...flac"
}

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, # Set the logging level (DEBUG, INFO, WARNING, ERROR, CRTICIAL)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("rfid_music.log"), # Log to a file
        logging.StreamHandler() # Also log to console
    ]
)

logger = logging.getLogger(__name__) # Create a logger for the script

# Debounce variables
last_card_id = None # Store the last detected card ID
last_read_time = 0  # Store the timestamp of the last read
DEBOUNCE_DELAY = 2  # Time in seconds to ignore repeated reads


def play_song(song_uri):
    """
    Send a play command to Moode for the specified song.
    """
    try:
        response = requests.get(f"{MOODE_API_BASE}playitem&arg={song_uri}")
        if response.status_code == 200:
            logger.info(f"Successfully played song: {song_uri}")
        else:
            logger.error(f"Failed to play song: {song_uri}. HTTP STatus: {response.status_code}")
    except Exception as e:
        logger.exception(f"Exception occurred while trying to play song: {song_uri}. Error: {e}")

def destroy():
    """
    Cleanup assigned resources before close
    """
    GPIO.cleanup()

# main script
try:
    logger.info("RFID Music Player started. Waiting for RFID cards...")
    while True:
        # Read RFID card
        card_id, text = reader.read()
        current_time = time.time()

        # Check if this is a duplicate read within the debounce delay
        if card_id == last_card_id and (current_time - last_read_time) < DEBOUNCE_DELAY:
            logger.debug(f"Ignoring duplicate read for card ID: {card_id}")
            continue

        # Update debounce variables
        last_card_id = card_id
        last_read_time = current_time

        logger.info(f"Card detected with ID: {card_id}") 

        # Check if card ID matches a song
        song_uri = RFID_TO_SONG.get(str(card_id))
        if song_uri:
            logger.info(f"Card ID matched. Playing song: {song_uri}")
            play_song(song_uri)
        else:
            logger.warning(f"Card ID {card_id} not recognized.")
finally:
    # Clean up the RFID reader
    destroy()
    logger.info("RFID Music Player stopped.")

