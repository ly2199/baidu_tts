"""Constants for the Baidu TTS integration."""

DOMAIN = "baidu_tts"

# Configuration keys
CONF_API_KEY = "api_key"
CONF_API_SECRET = "api_secret"
CONF_SPEED = "speed"
CONF_PITCH = "pitch"
CONF_VOLUME = "volume"
CONF_AUDIO_TYPE = "audio_type"
CONF_CUID = "cuid"

# Legacy option key, migrated to ATTR_VOICE ("voice") on setup
CONF_SPEAKER = "speaker"

# Default values
DEFAULT_SPEAKER = "1"  # 度小宇
DEFAULT_SPEED = 5
DEFAULT_PITCH = 5
DEFAULT_VOLUME = 5
DEFAULT_AUDIO_TYPE = "mp3"
DEFAULT_CUID = "homeassistant_baidu_tts"

# Baidu API endpoints
TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"
TTS_URL = "https://tsn.baidu.com/text2audio"

# Refresh the access token one day before it expires
TOKEN_REFRESH_AHEAD = 86400
DEFAULT_TOKEN_EXPIRES_IN = 2592000

# Baidu limits tex to ~1024 Chinese characters; keep chunks well below that
MAX_CHUNK_CHARS = 500

# Speaker options (per -> 发音人)
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
    "4146": "度嘻嘻",
}

# Audio type options
AUDIO_TYPE_OPTIONS = {
    "mp3": "MP3格式",
    "pcm-16k": "PCM 16kHz",
    "pcm-8k": "PCM 8kHz",
    "wav": "WAV格式",
}

# Audio type mapping for the Baidu API (aue parameter)
AUDIO_TYPE_MAPPING = {
    "mp3": 3,
    "pcm-16k": 4,
    "pcm-8k": 5,
    "wav": 6,
}

# Baidu TTS API error codes (err_no)
BAIDU_ERROR_CODES = {
    3: "认证错误，请检查API Key和Secret Key",
    16: "字符数超限",
    500: "不支持的编码格式",
    501: "输入参数不正确，请检查参数格式",
    502: "Token验证失败，请检查API Key和Secret Key",
    503: "合成后端错误",
    504: "合成后端繁忙，请稍后重试",
    282000: "服务器内部错误",
}
