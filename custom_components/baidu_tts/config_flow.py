"""Config flow for Baidu TTS."""
from __future__ import annotations
import logging
import voluptuous as vol
from typing import Any

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN, CONF_API_KEY, CONF_API_SECRET, CONF_SPEAKER,
    CONF_SPEED, CONF_PITCH, CONF_VOLUME, CONF_AUDIO_TYPE,
    CONF_CUID, DEFAULT_SPEAKER, DEFAULT_SPEED, DEFAULT_PITCH,
    DEFAULT_VOLUME, DEFAULT_AUDIO_TYPE, DEFAULT_CUID,
    SPEAKER_OPTIONS, AUDIO_TYPE_OPTIONS
)

_LOGGER = logging.getLogger(__name__)

class BaiduTTSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Baidu TTS."""
    
    VERSION = 1
    
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            # 验证API凭证
            try:
                import requests
                url = "https://aip.baidubce.com/oauth/2.0/token"
                params = {
                    "grant_type": "client_credentials",
                    "client_id": user_input[CONF_API_KEY],
                    "client_secret": user_input[CONF_API_SECRET]
                }
                
                response = await self.hass.async_add_executor_job(
                    requests.post, url, params
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "access_token" in data:
                        return self.async_create_entry(
                            title="百度TTS",
                            data=user_input,
                            options={
                                CONF_SPEAKER: user_input.get(CONF_SPEAKER, DEFAULT_SPEAKER),
                                CONF_SPEED: user_input.get(CONF_SPEED, DEFAULT_SPEED),
                                CONF_PITCH: user_input.get(CONF_PITCH, DEFAULT_PITCH),
                                CONF_VOLUME: user_input.get(CONF_VOLUME, DEFAULT_VOLUME),
                                CONF_AUDIO_TYPE: user_input.get(CONF_AUDIO_TYPE, DEFAULT_AUDIO_TYPE),
                                CONF_CUID: user_input.get(CONF_CUID, DEFAULT_CUID),
                            }
                        )
                    else:
                        errors["base"] = "invalid_auth"
                        _LOGGER.error("Authentication failed: %s", data)
                else:
                    errors["base"] = "cannot_connect"
                    _LOGGER.error("Connection failed: %s", response.status_code)
                    
            except Exception as err:
                _LOGGER.error("Error during authentication: %s", err)
                errors["base"] = "unknown"
        
        # 创建配置表单
        speaker_options = {k: f"{v} ({k})" for k, v in SPEAKER_OPTIONS.items()}
        
        data_schema = vol.Schema({
            vol.Required(CONF_API_KEY): str,
            vol.Required(CONF_API_SECRET): str,
            vol.Optional(CONF_CUID, default=DEFAULT_CUID): str,
            vol.Optional(CONF_SPEAKER, default=DEFAULT_SPEAKER): vol.In(speaker_options),
            vol.Optional(CONF_SPEED, default=DEFAULT_SPEED): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=15)
            ),
            vol.Optional(CONF_PITCH, default=DEFAULT_PITCH): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=15)
            ),
            vol.Optional(CONF_VOLUME, default=DEFAULT_VOLUME): vol.All(
                vol.Coerce(int), vol.Range(min=0, max=15)
            ),
            vol.Optional(CONF_AUDIO_TYPE, default=DEFAULT_AUDIO_TYPE): vol.In(AUDIO_TYPE_OPTIONS),
        })
        
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )
    
    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return BaiduTTSOptionsFlow(config_entry)

class BaiduTTSOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Baidu TTS."""
    
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry
    
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        
        # 创建选项表单
        speaker_options = {k: f"{v} ({k})" for k, v in SPEAKER_OPTIONS.items()}
        
        options_schema = vol.Schema({
            vol.Optional(
                CONF_SPEAKER,
                default=self._config_entry.options.get(CONF_SPEAKER, DEFAULT_SPEAKER)
            ): vol.In(speaker_options),
            vol.Optional(
                CONF_SPEED,
                default=self._config_entry.options.get(CONF_SPEED, DEFAULT_SPEED)
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=15)),
            vol.Optional(
                CONF_PITCH,
                default=self._config_entry.options.get(CONF_PITCH, DEFAULT_PITCH)
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=15)),
            vol.Optional(
                CONF_VOLUME,
                default=self._config_entry.options.get(CONF_VOLUME, DEFAULT_VOLUME)
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=15)),
            vol.Optional(
                CONF_AUDIO_TYPE,
                default=self._config_entry.options.get(CONF_AUDIO_TYPE, DEFAULT_AUDIO_TYPE)
            ): vol.In(AUDIO_TYPE_OPTIONS),
            vol.Optional(
                CONF_CUID,
                default=self._config_entry.options.get(CONF_CUID, DEFAULT_CUID)
            ): str,
        })
        
        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            errors=errors
        )
