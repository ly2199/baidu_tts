"""Baidu TTS API client."""
from __future__ import annotations

import asyncio
import logging
import struct
import time
from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import quote

import aiohttp

from homeassistant.exceptions import HomeAssistantError

from .const import (
    AUDIO_TYPE_MAPPING,
    BAIDU_ERROR_CODES,
    DEFAULT_TOKEN_EXPIRES_IN,
    MAX_CHUNK_CHARS,
    TOKEN_REFRESH_AHEAD,
    TOKEN_URL,
    TTS_URL,
)

_LOGGER = logging.getLogger(__name__)

SENTENCE_DELIMITERS = "。！？!?；;\n\r…"
SUB_DELIMITERS = "，,、：:"

_REQUEST_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "HomeAssistant-BaiduTTS/1.0.3",
}


def split_text(message: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split long text into chunks at sentence boundaries."""
    text = message.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + max_chars, length)
        if end < length:
            cut = -1
            for delimiters in (SENTENCE_DELIMITERS, SUB_DELIMITERS):
                for i in range(end - 1, start, -1):
                    if text[i] in delimiters:
                        cut = i + 1
                        break
                if cut > start:
                    break
            end = cut if cut > start else end
        chunks.append(text[start:end])
        start = end
    return chunks


def _extract_pcm(wav: bytes) -> bytes:
    """Return the raw PCM payload of the data chunk of a WAV fragment."""
    idx = wav.find(b"data")
    if idx == -1:
        return wav
    size = struct.unpack("<I", wav[idx + 4 : idx + 8])[0]
    return wav[idx + 8 : idx + 8 + size]


def concatenate_audio(chunks: list[bytes], audio_type: str) -> bytes:
    """Concatenate audio fragments into a single playable stream."""
    if not chunks:
        return b""
    if len(chunks) == 1 or audio_type != "wav":
        # MP3 and raw PCM frames can be concatenated directly
        return b"".join(chunks)

    data_idx = chunks[0].find(b"data")
    if data_idx == -1:
        return b"".join(chunks)
    header = bytearray(chunks[0][: data_idx + 8])
    pcm = b"".join(_extract_pcm(chunk) for chunk in chunks)
    struct.pack_into("<I", header, 4, len(header) - 8 + len(pcm))
    struct.pack_into("<I", header, data_idx + 4, len(pcm))
    return bytes(header) + pcm


class BaiduTTSClient:
    """Client for the Baidu TTS REST API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        api_key: str,
        api_secret: str,
        cuid: str,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._api_key = api_key
        self._api_secret = api_secret
        self._cuid = cuid
        self._access_token: str | None = None
        self._token_expiry = 0.0
        self._token_lock = asyncio.Lock()

    @property
    def cuid(self) -> str:
        """Return the client user id."""
        return self._cuid

    @cuid.setter
    def cuid(self, value: str) -> None:
        """Update the client user id."""
        self._cuid = value

    async def async_get_access_token(self, force_refresh: bool = False) -> str:
        """Return a valid access token, fetching it when needed."""
        async with self._token_lock:
            if (
                not force_refresh
                and self._access_token
                and time.time() < self._token_expiry
            ):
                return self._access_token

            params = {
                "grant_type": "client_credentials",
                "client_id": self._api_key,
                "client_secret": self._api_secret,
            }
            try:
                response = await self._session.post(
                    TOKEN_URL,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10),
                )
                data: dict[str, Any] = await response.json(content_type=None)
            except (TimeoutError, aiohttp.ClientError) as err:
                raise HomeAssistantError(
                    f"连接百度认证服务失败: {err}"
                ) from err

            if "access_token" not in data:
                error = data.get("error_description") or data.get("error") or data
                raise HomeAssistantError(f"获取百度访问令牌失败: {error}")

            self._access_token = data["access_token"]
            expires_in = data.get("expires_in", DEFAULT_TOKEN_EXPIRES_IN)
            self._token_expiry = time.time() + max(
                int(expires_in) - TOKEN_REFRESH_AHEAD, 60
            )
            _LOGGER.debug("Successfully obtained Baidu access token")
            return self._access_token

    def _build_payload(self, token: str, text: str, options: dict[str, Any]) -> str:
        """Build the form payload for the Baidu TTS API."""
        # The API expects tex to be URL-encoded twice; aiohttp does not
        # re-encode a raw string body, so encode twice here.
        encoded_text = quote(quote(text, safe=""), safe="")
        aue = AUDIO_TYPE_MAPPING.get(options["audio_type"], 3)
        return (
            f"tok={token}&tex={encoded_text}&cuid={self._cuid}&ctp=1&lan=zh"
            f"&spd={options['speed']}&pit={options['pitch']}&vol={options['volume']}"
            f"&per={options['speaker']}&aue={aue}"
        )

    async def _synthesize_chunk(
        self, text: str, options: dict[str, Any], retry_on_auth: bool = True
    ) -> bytes:
        """Synthesize a single text chunk and return the audio bytes."""
        token = await self.async_get_access_token()
        payload = self._build_payload(token, text, options)
        try:
            response = await self._session.post(
                TTS_URL,
                data=payload.encode("utf-8"),
                headers=_REQUEST_HEADERS,
                timeout=aiohttp.ClientTimeout(total=30),
            )
            data = await response.read()
        except (TimeoutError, aiohttp.ClientError) as err:
            raise HomeAssistantError(f"连接百度TTS服务失败: {err}") from err

        if response.headers.get("Content-Type", "").startswith("audio/"):
            return data

        try:
            error_data = await response.json(content_type=None)
        except ValueError:
            raise HomeAssistantError(
                f"百度TTS合成失败，服务器返回: HTTP {response.status}"
            ) from None

        err_no = error_data.get("err_no")
        err_msg = error_data.get("err_msg")
        message = BAIDU_ERROR_CODES.get(err_no, f"百度TTS错误: {err_no} ({err_msg})")
        if err_no == 502 and retry_on_auth:
            _LOGGER.debug("Access token rejected, refreshing and retrying")
            await self.async_get_access_token(force_refresh=True)
            return await self._synthesize_chunk(text, options, retry_on_auth=False)
        raise HomeAssistantError(message)

    async def async_synthesize(
        self, message: str, options: dict[str, Any]
    ) -> bytes:
        """Synthesize a message, splitting long text as needed."""
        chunks = split_text(message)
        if not chunks:
            raise HomeAssistantError("待合成文本为空")
        if len(chunks) > 1:
            _LOGGER.debug("Split message into %d chunks", len(chunks))
        audio = [
            await self._synthesize_chunk(chunk, options) for chunk in chunks
        ]
        return concatenate_audio(audio, options["audio_type"])

    async def async_synthesize_stream(
        self, message: str, options: dict[str, Any]
    ) -> AsyncIterator[bytes]:
        """Yield audio per chunk so playback can start early."""
        chunks = split_text(message)
        if not chunks:
            raise HomeAssistantError("待合成文本为空")
        for chunk in chunks:
            yield await self._synthesize_chunk(chunk, options)
