"""Config flow for the Baidu TTS integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.components.tts import ATTR_VOICE
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    AUDIO_TYPE_OPTIONS,
    CONF_API_KEY,
    CONF_API_SECRET,
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
    TOKEN_URL,
)

_LOGGER = logging.getLogger(__name__)

SPEAKER_SELECTOR = {k: f"{v} ({k})" for k, v in SPEAKER_OPTIONS.items()}


async def _async_validate_credentials(
    hass: HomeAssistant, api_key: str, api_secret: str
) -> str | None:
    """Validate API credentials, return an error key or None on success."""
    params = {
        "grant_type": "client_credentials",
        "client_id": api_key,
        "client_secret": api_secret,
    }
    try:
        response = await async_get_clientsession(hass).post(
            TOKEN_URL, params=params, timeout=aiohttp.ClientTimeout(total=10)
        )
        data = await response.json(content_type=None)
    except (TimeoutError, aiohttp.ClientError) as err:
        _LOGGER.error("Cannot connect to Baidu auth service: %s", err)
        return "cannot_connect"

    if "access_token" in data:
        return None
    _LOGGER.error("Baidu authentication failed: %s", data)
    return "invalid_auth"


def _options_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Build the shared options schema."""
    return vol.Schema(
        {
            vol.Required(
                ATTR_VOICE, default=defaults.get(ATTR_VOICE, DEFAULT_SPEAKER)
            ): vol.In(SPEAKER_SELECTOR),
            vol.Required(
                CONF_SPEED, default=defaults.get(CONF_SPEED, DEFAULT_SPEED)
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=15)),
            vol.Required(
                CONF_PITCH, default=defaults.get(CONF_PITCH, DEFAULT_PITCH)
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=15)),
            vol.Required(
                CONF_VOLUME, default=defaults.get(CONF_VOLUME, DEFAULT_VOLUME)
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=15)),
            vol.Required(
                CONF_AUDIO_TYPE,
                default=defaults.get(CONF_AUDIO_TYPE, DEFAULT_AUDIO_TYPE),
            ): vol.In(AUDIO_TYPE_OPTIONS),
            vol.Optional(
                CONF_CUID, default=defaults.get(CONF_CUID, DEFAULT_CUID)
            ): str,
        }
    )


class BaiduTTSConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Baidu TTS."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            error = await _async_validate_credentials(
                self.hass, user_input[CONF_API_KEY], user_input[CONF_API_SECRET]
            )
            if error is None:
                options = {
                    key: value
                    for key, value in user_input.items()
                    if key not in (CONF_API_KEY, CONF_API_SECRET)
                }
                return self.async_create_entry(
                    title="百度TTS",
                    data={
                        CONF_API_KEY: user_input[CONF_API_KEY],
                        CONF_API_SECRET: user_input[CONF_API_SECRET],
                    },
                    options=options,
                )
            errors["base"] = error

        schema = vol.Schema(
            {
                vol.Required(CONF_API_KEY): str,
                vol.Required(CONF_API_SECRET): str,
            }
        ).extend(_options_schema({}).schema)
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return BaiduTTSOptionsFlow()


class BaiduTTSOptionsFlow(OptionsFlow):
    """Handle options flow for Baidu TTS."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=_options_schema(dict(self.config_entry.options)),
        )
