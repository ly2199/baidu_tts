"""Baidu TTS platform for Home Assistant."""
from __future__ import annotations
import logging
import time
import requests
import urllib.parse
from typing import Any

from homeassistant.components.tts import (
    CONF_LANG,
    TextToSpeechEntity,
    TtsAudioType,
    Voice,
    ATTR_AUDIO_OUTPUT,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN, CONF_API_KEY, CONF_API_SECRET, CONF_SPEAKER,
    CONF_SPEED, CONF_PITCH, CONF_VOLUME, CONF_AUDIO_TYPE,
    CONF_CUID, AUDIO_TYPE_MAPPING, SPEAKER_OPTIONS,
    DEFAULT_SPEAKER, DEFAULT_SPEED, DEFAULT_PITCH,
    DEFAULT_VOLUME, DEFAULT_AUDIO_TYPE, DEFAULT_CUID
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Baidu TTS from a config entry."""
    _LOGGER.info("Setting up Baidu TTS entity for entry: %s", config_entry.entry_id)
    
    # 创建TTS实体
    entity = BaiduTTSEntity(config_entry)
    async_add_entities([entity])
    
    # 存储实体ID
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = entity

class BaiduTTSEntity(TextToSpeechEntity):
    """Baidu TTS entity."""
    
    _attr_name = "百度TTS"
    
    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize Baidu TTS entity."""
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}-tts"
        
        # 设备信息
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": "百度TTS服务",
            "manufacturer": "百度",
            "model": "语音合成API",
            "entry_type": DeviceEntryType.SERVICE,
        }
        
        # 从配置获取API凭证
        self._api_key = config_entry.data[CONF_API_KEY]
        self._api_secret = config_entry.data[CONF_API_SECRET]
        
        # 访问令牌缓存
        self._access_token = None
        self._token_expiry = 0
        
        # 从options获取配置
        self._update_options()

    def _update_options(self):
        """更新选项配置"""
        options = self._config_entry.options
        
        self._default_speaker = options.get(CONF_SPEAKER, DEFAULT_SPEAKER)
        self._default_speed = options.get(CONF_SPEED, DEFAULT_SPEED)
        self._default_pitch = options.get(CONF_PITCH, DEFAULT_PITCH)
        self._default_volume = options.get(CONF_VOLUME, DEFAULT_VOLUME)
        self._audio_type = options.get(CONF_AUDIO_TYPE, DEFAULT_AUDIO_TYPE)
        self._cuid = options.get(CONF_CUID, DEFAULT_CUID)
        
        _LOGGER.debug(
            "Updated options: speaker=%s, speed=%s, pitch=%s, volume=%s, audio_type=%s",
            self._default_speaker, self._default_speed, self._default_pitch,
            self._default_volume, self._audio_type
        )

    async def async_added_to_hass(self) -> None:
        """当实体添加到Home Assistant时调用."""
        self._update_options()
        
        # 监听选项更新
        self._config_entry.async_on_unload(
            self._config_entry.add_update_listener(self._async_options_updated)
        )

    async def _async_options_updated(
        self, hass: HomeAssistant, config_entry: ConfigEntry
    ) -> None:
        """处理选项更新."""
        _LOGGER.info("Options updated for Baidu TTS")
        self._update_options()

    @property
    def default_language(self) -> str:
        """返回默认语言."""
        return "zh"

    @property
    def supported_languages(self) -> list[str]:
        """返回支持的语言列表."""
        return ["zh"]

    @property
    def default_voice(self) -> str:
        """返回默认语音."""
        return self._default_speaker

    @property
    def supported_voices(self) -> list[Voice]:
        """返回支持的语音列表."""
        voices = []
        for speaker_id, speaker_name in SPEAKER_OPTIONS.items():
            voices.append(Voice(
                voice_id=speaker_id,
                name=speaker_name,
                language="zh"
            ))
        return voices

    @property
    def supported_options(self) -> list[str]:
        """返回支持的选项列表."""
        return ["speaker", "speed", "pitch", "volume", ATTR_AUDIO_OUTPUT]

    @property
    def default_options(self) -> dict[str, Any]:
        """返回默认选项."""
        return {
            "speaker": self._default_speaker,
            "speed": self._default_speed,
            "pitch": self._default_pitch,
            "volume": self._default_volume,
        }

    def _get_access_token(self) -> str | None:
        """从百度API获取访问令牌."""
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self._api_key,
            "client_secret": self._api_secret
        }
        
        try:
            _LOGGER.debug("Requesting access token from Baidu")
            response = requests.post(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "access_token" in data:
                self._access_token = data["access_token"]
                # Token有效期为30天 (2592000秒)，我们提前1天刷新
                self._token_expiry = time.time() + 2592000 - 86400
                _LOGGER.info("Successfully obtained access token")
                return self._access_token
            else:
                error_msg = data.get("error_description", "Unknown error")
                _LOGGER.error("Failed to get access token: %s", error_msg)
                return None
                
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Network error getting access token: %s", err)
            return None
        except Exception as err:
            _LOGGER.error("Unexpected error getting access token: %s", err)
            return None

    def _double_urlencode(self, text: str) -> str:
        """双URL编码，百度API要求."""
        first_encode = urllib.parse.quote(text, safe='')
        second_encode = urllib.parse.quote(first_encode, safe='')
        return second_encode

    def _build_payload(self, access_token: str, message: str, options: dict[str, Any]) -> str:
        """构建百度API请求的payload字符串."""
        # 合并选项
        merged_options = {**self.default_options, **(options or {})}
        
        # 提取参数
        speaker = merged_options.get("speaker", self._default_speaker)
        speed = merged_options.get("speed", self._default_speed)
        pitch = merged_options.get("pitch", self._default_pitch)
        volume = merged_options.get("volume", self._default_volume)
        
        # 音频类型处理：优先使用options中的audio_output，否则使用配置的audio_type
        audio_output = options.get(ATTR_AUDIO_OUTPUT) if options else None
        audio_type = audio_output if audio_output else self._audio_type
        
        # 双重编码文本
        encoded_text = self._double_urlencode(message)
        
        # 构建payload字符串 - 按照百度API示例格式
        # 注意：这里要按照百度API示例的格式，直接拼接参数
        payload = f"tok={access_token}&tex={encoded_text}&cuid={self._cuid}&ctp=1&lan=zh&spd={speed}&pit={pitch}&vol={volume}&per={speaker}&aue={AUDIO_TYPE_MAPPING.get(audio_type, 3)}"
        
        _LOGGER.debug(
            "构建payload: speaker=%s, speed=%s, pitch=%s, volume=%s, audio_type=%s",
            speaker, speed, pitch, volume, audio_type
        )
        _LOGGER.debug("编码后的文本: %s", encoded_text[:100] + "..." if len(encoded_text) > 100 else encoded_text)
        
        return payload

    async def async_get_tts_audio(
        self,
        message: str,
        language: str,
        options: dict[str, Any] | None = None,
    ) -> TtsAudioType:
        """将文本转换为语音."""
        _LOGGER.debug("Processing TTS request: '%s'", message[:50])
        
        try:
            # 获取或刷新访问令牌
            current_time = time.time()
            if not self._access_token or current_time > self._token_expiry:
                _LOGGER.info("Access token expired or missing, refreshing...")
                token = await self.hass.async_add_executor_job(self._get_access_token)
                if not token:
                    _LOGGER.error("Cannot get access token, aborting synthesis")
                    raise Exception("无法获取访问令牌")
            
            # 构建payload
            payload = self._build_payload(self._access_token, message, options)
            
            # 发起API请求
            url = "https://tsn.baidu.com/text2audio"
            
            def _make_request():
                return requests.post(
                    url,
                    data=payload.encode('utf-8'),  # 注意：直接发送编码后的字节串
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Accept": "*/*",
                        "User-Agent": "HomeAssistant-BaiduTTS/1.0.0"
                    },
                    timeout=30
                )
            
            response = await self.hass.async_add_executor_job(_make_request)
            
            # 检查响应
            content_type = response.headers.get("Content-Type", "")
            _LOGGER.debug(
                "TTS响应: 状态码=%s, Content-Type=%s, 大小=%d字节",
                response.status_code, content_type, len(response.content)
            )
            
            # 检查是否是音频响应
            if content_type.startswith("audio/"):
                audio_data = response.content
                _LOGGER.info("TTS合成成功! 音频大小: %d bytes", len(audio_data))
                
                # 从payload中提取音频类型
                import re
                aue_match = re.search(r'aue=(\d+)', payload)
                if aue_match:
                    aue_value = aue_match.group(1)
                    # 反向查找音频类型
                    audio_type_map_reverse = {v: k for k, v in AUDIO_TYPE_MAPPING.items()}
                    audio_type = audio_type_map_reverse.get(int(aue_value), "mp3")
                else:
                    audio_type = "mp3"
                
                # 根据音频类型返回对应的MIME类型
                if audio_type == "mp3":
                    return "mp3", audio_data
                elif audio_type == "wav":
                    return "wav", audio_data
                elif audio_type == "pcm-16k" or audio_type == "pcm-8k":
                    return "raw", audio_data
                else:
                    # 默认返回mp3
                    return "mp3", audio_data
                    
            else:
                # 尝试解析错误
                try:
                    error_data = response.json()
                    error_code = error_data.get("err_no")
                    error_msg = error_data.get("err_msg", "未知错误")
                    
                    _LOGGER.error("百度TTS API错误: 代码=%s, 消息=%s", error_code, error_msg)
                    
                    if error_code == 502:
                        # Token失效，清除缓存
                        self._access_token = None
                        raise Exception("Token验证失败，请检查API Key和Secret Key")
                    elif error_code == 501:
                        raise Exception("输入参数不正确，请检查参数格式")
                    elif error_code == 503:
                        raise Exception("合成后端错误")
                    elif error_code == 16:
                        raise Exception("字符数超限")
                    else:
                        raise Exception(f"百度TTS错误: {error_msg}")
                        
                except ValueError:
                    # 不是JSON响应
                    _LOGGER.error("百度TTS返回了非音频内容。状态码: %s, 内容: %s", 
                                 response.status_code, response.text[:200])
                    raise Exception(f"TTS合成失败，服务器返回: {response.status_code}")
                    
        except Exception as err:
            _LOGGER.error("TTS合成失败: %s", err, exc_info=True)
            raise
