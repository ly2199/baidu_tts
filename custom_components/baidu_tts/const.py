"""Constants for Baidu TTS integration."""

DOMAIN = "baidu_tts"
PLATFORMS = ["tts"]

# Configuration keys
CONF_API_KEY = "api_key"
CONF_API_SECRET = "api_secret"
CONF_SPEAKER = "speaker"
CONF_SPEED = "speed"
CONF_PITCH = "pitch"
CONF_VOLUME = "volume"
CONF_AUDIO_TYPE = "audio_type"
CONF_CUID = "cuid"

# Default values
DEFAULT_SPEAKER = "1"  # 度小宇
DEFAULT_SPEED = 5
DEFAULT_PITCH = 5
DEFAULT_VOLUME = 5
DEFAULT_AUDIO_TYPE = "mp3"
DEFAULT_CUID = "homeassistant_baidu_tts"

# Speaker options
SPEAKER_OPTIONS = {
    "1": "度小宇",
    "0": "度小美", 
    "3": "度逍遥(基础)",
    "4": "度丫丫",
    "5003": "度逍遥(精品)",
    "5118": "度小鹿",
    "106": "度博文",
    "110": "度小童",
    "111": "度小萌",
    "103": "度米朵",
    "5": "度小娇",
    "4146": "度嘻嘻"
}

# Audio type options
AUDIO_TYPE_OPTIONS = {
    "mp3": "MP3格式",
    "pcm-16k": "PCM 16kHz",
    "pcm-8k": "PCM 8kHz",
    "wav": "WAV格式"
}

# Audio type mapping for API
AUDIO_TYPE_MAPPING = {
    "mp3": 3,
    "pcm-16k": 4,
    "pcm-8k": 5,
    "wav": 6
}

# TTS options for Home Assistant
TTS_OPTIONS = ["speaker", "speed", "pitch", "volume"]
