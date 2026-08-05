from google.genai.types import SafetySetting, HarmCategory, HarmBlockThreshold
from pathlib import Path
import logging
import os
import sys
from dotenv import load_dotenv

load_dotenv()

#  ===FEATURES===
# I strongly recommend enabling the Spotify API to ensure the music bot functions properly.
# Make sure to specify SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET in the .env file.
# If the Spotify API is disabled, please check ./commands/lyrics.py for adjustments.
SPOTIFY_API_ENABLED = True
SPOTIFY_ENABLED = True
DEEZER_ENABLED = False
DEFAULT_STREAMING_SERVICE = 'spotify/deezer'
GEMINI_ENABLED = False # Don't forget to whitelist servers for the chatbot via /database commands !
PINECONE_ENABLED = False
ALLOW_CHATBOT_IN_DMS = False # Allow everyone to use the bot in dms.

# IN DEVELOPMENT: Used for compatibility purposes
# Make sure to create an OpenAI API key here https://platform.openai.com/api-keys
# If enabled, the OpenAI model will be used only for the chatbot for now
OPENAI_ENABLED = False

# ===CHATBOT MODELS===
GEMINI_MODEL = 'gemini-3.5-flash'
GEMINI_UTILS_MODELS = [
    'gemini-3-flash-preview',
    'gemini-3.1-flash-lite',
    'gemini-2.5-flash',
    'gemini-2.0-flash',
] # Used lyrics, example sentences and memory management
OPENAI_MODEL = 'gpt-4.1-mini-2025-04-14'

# Display names
GEMINI_MODEL_DISPLAY_NAME = 'Gemini 3.5 Flash'
OPENAI_MODEL_DISPLAY_NAME = "GPT-4.1 mini"

#  ===SETTINGS===
# Paths
COMMANDS_FOLDER = Path('./commands')
TEMP_FOLDER = Path('.') / 'temp'
PREMIUM_CHANNEL_ID = None # Upload files too big to a channel in a boosted server instead
DB_PATH = Path("config.sqlite")

# Production health monitoring. HEALTH_MONITOR_INTERVAL is intentionally the
# single cadence for both the observable state and systemd watchdog heartbeat.
HEALTH_MONITOR_ENABLED: bool = True
HEALTH_MONITOR_INTERVAL: int = 20
HEALTH_RUN_DIR: Path = Path(os.getenv("UGOKU_RUN_DIR") or "/run/ugoku")
HEALTH_STATE_FILE: Path = Path(
    os.getenv("UGOKU_HEALTH_STATE_FILE") or str(HEALTH_RUN_DIR / "health.json")
)
HEALTH_STATE_MODE: int = 0o644
HEALTH_FAIL_COUNT_FILE: Path = HEALTH_RUN_DIR / "fail.count"
HEALTH_INCIDENT_FILE: Path = HEALTH_RUN_DIR / "incident.json"
HEALTH_ALERT_OUTBOX_FILE: Path = HEALTH_RUN_DIR / "alert-outbox.json"
HEALTH_GATEWAY_LATENCY_THRESHOLD_MS: int = 10_000
HEALTH_LOOP_LAG_THRESHOLD_MS: int = 3_000
HEALTH_STALE_THRESHOLD: int = 180
HEALTH_READY_GRACE: int = 60
HEALTH_FAILURE_THRESHOLD: int = 2
HEALTH_SHUTDOWN_BUDGET: int = 20
HEALTH_FORCE_CLEANUP_BUDGET: int = 8
HEALTH_AUDIO_PROBE_COOLDOWN: int = 60
HEALTH_AUDIO_PROBE_TIMEOUT: float = 15.0
HEALTH_AUDIO_PROBE_BYTES: int = 8192
HEALTH_AUDIO_PROBE_TRACK_ID: str | None = os.getenv(
    "UGOKU_HEALTH_AUDIO_PROBE_TRACK_ID"
)
HEALTH_ALERT_TIMEOUT: float = 5.0

# RESOURCE_BLOCKED predicate thresholds.
HEALTH_FFMPEG_ORPHAN_THRESHOLD: int = 0
HEALTH_VOICE_CONNECT_STUCK_S: int = 30
HEALTH_LIBRESPOT_STALE_S: int = 60

# End-to-end recovery SLA and the upper bound assigned to each operation.
HEALTH_SLA_TOTAL_S: int = 300
HEALTH_SLA_DETECT_S: int = 225
HEALTH_SLA_RESTART_TRIGGER_S: int = 5
HEALTH_SLA_STOP_S: int = 25
HEALTH_SLA_RESTART_SEC_S: int = 5
HEALTH_SLA_BOOT_READY_S: int = 30
HEALTH_SLA_RECOVERY_ALERT_S: int = 5

# Alerting is external to the bot loop. This value is consumed by the external
# healthcheck only; ADMIN_OWNER_IDS protects the in-bot /health command.
ADMIN_ALERT_WEBHOOK: str | None = os.getenv("UGOKU_ALERT_WEBHOOK")
ADMIN_OWNER_IDS: list[int] = [
    int(value.strip())
    for value in os.getenv("UGOKU_ADMIN_OWNER_IDS", "").split(",")
    if value.strip()
]

# Cache control & preloading
AGRESSIVE_CACHING = False # Avoid persistent reader workers when Librespot connections are unstable.
PRELOAD_TRACKS = 1 # Number of tracks to preload
CACHE_SIZE = 100  # Cache size limit (in number of files)
CACHE_EXPIRY = 2592000  # Cache expiry time (in seconds). Default is one month

# VC and audio bot behavior
AUTO_LEAVE_DURATION = 900 # Duration before killing an audio session (in seconds)
DEEZER_REFRESH_INTERVAL = 3600 # How often should the bot refresh the Deezer session
SPOTIFY_REFRESH_INTERVAL = 180 # How often should the bot check and refresh the Spotify session
SPOTIFY_TOP_COUNTRY = 'JP' # Used to establish an artist's top tracks, can be changed to any country you want
DEFAULT_EMBED_COLOR = (237, 205, 85) # If the Now playing song doesn't have a cover
DEFAULT_AUDIO_VOLUME = 20 # Linear scale! The recommended value is around 20.
DEFAULT_ONSEI_VOLUME = 100 # Audio works are generally quieter for a higher dynamic range
DEFAULT_AUDIO_BITRATE = 320 # From 6 to 510 kbps (opus output)
IMPULSE_RESPONSE_PARAMS = {
    'bass boost (mono)': {
        'left_ir_file': 'bass.wav',
        'right_ir_file': 'bass.wav',
        'dry': 1,
        'wet': 7,
        'volume_multiplier': 0.3,
    },
    'reverb (mono)': {
        'left_ir_file': 'reverb.wav',
        'right_ir_file': 'reverb.wav',
        'dry': 7,
        'wet': 9,
        'volume_multiplier': 1.3
    },
    'north church': {
        'left_ir_file': 'north_church_L.wav',
        'right_ir_file': 'north_church_R.wav',
        'dry': 7,
        'wet': 5,
        'volume_multiplier': 1.3
    },
    'cinema': {
        'left_ir_file': 'cinema_L.wav',
        'right_ir_file': 'cinema_R.wav',
        'dry': 7,
        'wet': 3,
        'volume_multiplier': 0.8
    },
    'bass XXL': {
        'left_ir_file': 'bass_xxl_L.wav',
        'right_ir_file': 'bass_xxl_R.wav',
        'dry': 7,
        'wet': 2,
        'volume_multiplier': 0.6
    },
    'Raum airy default': {
        'left_ir_file': 'raum_default_airy_L.wav',
        'right_ir_file': 'raum_default_airy_R.wav',
        'dry': 10,
        'wet': 10,
        'volume_multiplier': 1
    },
    'Raum grounded default': {
        'left_ir_file': 'raum_default_grounded_L.wav',
        'right_ir_file': 'raum_default_grounded_R.wav',
        'dry': 10,
        'wet': 10,
        'volume_multiplier': 0.75
    },
    'Raum size 100%, decay 2s': {
        'left_ir_file': 'raum_max_size_L.wav',
        'right_ir_file': 'raum_max_size_R.wav',
        'dry': 10,
        'wet': 10,
        'volume_multiplier': 0.4
    }
} # (Advanced) Add your own audio effects to the /audio-effect list with an impulse response file in ./audio-ir

# Onsei filters
ONSEI_WHITELIST = ['mp3'] # Onsei tracks with one of these extensions and in a folder name containing one of these words will be chosen
ONSEI_BLACKLIST = ['なし'] # Tracks containing one of these words will be blacklisted

# Chatbot settings
CHATBOT_CHANNEL_WHITELIST = {} # All channel/thread ids allowed to use the chatbot
CHATBOT_PREFIX = '!' # Prefix to trigger the chatbot
GEMINI_PREFIX = '-' # If OpenAI is enabled, CHATBOT_PREFIX+GEMINI_PREFIX will force to use Gemini instead
GEMINI_THINKING_LEVEL = "minimal" # minimal (except on 3.1 Pro), low, medium or high
CHATBOT_TIMEOUT = 300 # Time before disabling continuous chat (in seconds, enabled with double prefix)
CHATBOT_TIMEZONE = 'Asia/Tokyo'
CHATBOT_TEMPERATURE = 1.0 # From 0.0 to 2.0. Specifies the randomness/creativity of the chatbot
CHATBOT_EMOTE_FREQUENCY = 1/5 # How often the emotes generated by gemini, will be shown. 
CHATBOT_MAX_OUTPUT_TOKEN = 3000 # A too low max output token can result in a None ("filtered") output
CHATBOT_HISTORY_SIZE = 20 # How many messages (Q+A) to keep in chat history
CHATBOT_MAX_CONTENT_SIZE = {
    'text': 200000,
    'audio': 10000000,
    'image': 7000000,
    'application': 2000000
} # Max length of an attachment, in bytes
PINECONE_RECALL_WINDOW = 4
PINECONE_INDEX_NAME = 'ugoku2'
GEMINI_SAFETY_SETTINGS = [
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=HarmBlockThreshold.BLOCK_NONE
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=HarmBlockThreshold.BLOCK_NONE,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=HarmBlockThreshold.BLOCK_NONE,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=HarmBlockThreshold.BLOCK_NONE,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=HarmBlockThreshold.BLOCK_NONE,
    ),
] # See https://ai.google.dev/gemini-api/docs/safety-settings
LANGUAGES = [
    # Put any language you want to support in /translate command.
    # Has to be supported by the LLM.
    "Arabic", "Bengali", "Dutch", "English", "French", "German", "Greek",
    "Hebrew", "Hindi", "Indonesian", "Italian", "Japanese",
    "Korean", "Mandarin Chinese", "Persian", "Polish", "Portuguese",
    "Russian", "Spanish", "Swedish", "Thai", "Turkish", "Vietnamese"
]

# Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
