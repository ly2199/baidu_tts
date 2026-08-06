"""Baidu TTS platform for Home Assistant."""
from __future__ import annotations

from collections.abc import AsyncGenerator, Mapping
import logging
from typing import Any

from homeassistant.components.tts import (
    ATTR_AUDIO_OUTPUT,
    ATTR_VOICE,
    TTSAudioRequest,
    TTSAudioResponse,
    TextToSpeechEntity,
    TtsAudioType,
    Voice,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import BaiduTTSClient
from .const import (
    AUDIO_TYPE_MAPPING,
    CONF_AUDIO_TYPE,
    CONF_CUID,
    CONF_PITCH,
    CONF_SPEED,
    CONF_VOLUME,
    DEFAULT_AUDIO_TYPE,
    DEFAULT_CUID,
    DEFAULT_PITCH,
    DEFAULT_SPEED,
    DEFAULT_SPEAKER,
    DEFAULT_VOLUME,
    DOMAIN,
    SPEAKER_OPTIONS,
)

_LOGGER = logging.getLogger(__name__)

SUPPORTED_OPTIONS = [ATTR_VOICE, CONF_SPEED, CONF_PITCH, CONF_VOLUME, ATTR_AUDIO_OUTPUT]
AUDIO_EXTENSION = {"mp3": "mp3", "wav": "wav", "pcm-16k": "raw", "pcm-8k": "raw"}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Baidu TTS entity from a config entry."""
    client: BaiduTTSClient = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([BaiduTTSEntity(config_entry, client)])


class BaiduTTSEntity(TextToSpeechEntity):
    """Baidu TTS entity."""

    _attr_default_language = "zh"
    _attr_supported_languages = ["zh"]
    _attr_supported_options = SUPPORTED_OPTIONS
    _attr_icon = "mdi:speaker-message"
    _attr_name = None

    def __init__(self, config_entry: ConfigEntry, client: BaiduTTSClient) -> None:
        """Initialize the entity."""
        self._config_entry = config_entry
        self._client = client
        self._attr_unique_id = f"{config_entry.entry_id}-tts"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name="百度TTS",
            manufacturer="百度",
            model="语音合成API",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def _options(self) -> dict[str, Any]:
        """Return the current options from the config entry."""
        options = self._config_entry.options
        return {
            "speaker": options.get(ATTR_VOICE, DEFAULT_SPEAKER),
            "speed": options.get(CONF_SPEED, DEFAULT_SPEED),
            "pitch": options.get(CONF_PITCH, DEFAULT_PITCH),
            "volume": options.get(CONF_VOLUME, DEFAULT_VOLUME),
            "audio_type": options.get(CONF_AUDIO_TYPE, DEFAULT_AUDIO_TYPE),
            "cuid": options.get(CONF_CUID, DEFAULT_CUID),
        }

    @property
    def default_options(self) -> Mapping[str, Any]:
        """Return the default options."""
        options = self._options
        return {
            ATTR_VOICE: options["speaker"],
            CONF_SPEED: options["speed"],
            CONF_PITCH: options["pitch"],
            CONF_VOLUME: options["volume"],
        }

    @callback
    def async_get_supported_voices(self, language: str) -> list[Voice] | None:
        """Return the list of supported voices."""
        if language != "zh":
            return None
        return [
            Voice(voice_id=speaker_id, name=speaker_name)
            for speaker_id, speaker_name in SPEAKER_OPTIONS.items()
        ]

    def _resolve_options(self, options: dict[str, Any]) -> dict[str, Any]:
        """Merge request options with the configured defaults."""
        defaults = self._options
        audio_type = options.get(ATTR_AUDIO_OUTPUT) or defaults["audio_type"]
        if audio_type not in AUDIO_TYPE_MAPPING:
            audio_type = DEFAULT_AUDIO_TYPE
        return {
            "speaker": options.get(ATTR_VOICE, defaults["speaker"]),
            "speed": int(options.get(CONF_SPEED, defaults["speed"])),
            "pitch": int(options.get(CONF_PITCH, defaults["pitch"])),
            "volume": int(options.get(CONF_VOLUME, defaults["volume"])),
            "audio_type": audio_type,
        }

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any]
    ) -> TtsAudioType:
        """Convert text to speech."""
        resolved = self._resolve_options(options)
        _LOGGER.debug(
            "Synthesizing %d chars with speaker=%s, format=%s",
            len(message), resolved["speaker"], resolved["audio_type"],
        )
        data = await self._client.async_synthesize(message, resolved)
        return AUDIO_EXTENSION[resolved["audio_type"]], data

    async def async_stream_tts_audio(
        self, request: TTSAudioRequest
    ) -> TTSAudioResponse:
        """Stream synthesized audio chunk by chunk."""
        message = "".join([chunk async for chunk in request.message_gen])
        resolved = self._resolve_options(request.options)
        extension = AUDIO_EXTENSION[resolved["audio_type"]]

        async def data_gen() -> AsyncGenerator[bytes]:
            async for chunk in self._client.async_synthesize_stream(
                message, resolved
            ):
                yield chunk

        return TTSAudioResponse(extension, data_gen())
