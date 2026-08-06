"""The Baidu TTS integration."""
from __future__ import annotations

import logging

from homeassistant.components.tts import ATTR_VOICE
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import BaiduTTSClient
from .const import (
    CONF_API_KEY,
    CONF_API_SECRET,
    CONF_CUID,
    CONF_SPEAKER,
    DEFAULT_CUID,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.TTS]


def _migrate_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Rename the legacy 'speaker' option to the standard 'voice' key."""
    if CONF_SPEAKER in entry.options and ATTR_VOICE not in entry.options:
        options = dict(entry.options)
        options[ATTR_VOICE] = options.pop(CONF_SPEAKER)
        hass.config_entries.async_update_entry(entry, options=options)
        _LOGGER.info("Migrated option '%s' to '%s'", CONF_SPEAKER, ATTR_VOICE)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Baidu TTS from a config entry."""
    _migrate_options(hass, entry)

    domain_data: dict[str, BaiduTTSClient] = hass.data.setdefault(DOMAIN, {})
    client = domain_data.get(entry.entry_id)
    if client is None:
        client = BaiduTTSClient(
            session=async_get_clientsession(hass),
            api_key=entry.data[CONF_API_KEY],
            api_secret=entry.data[CONF_API_SECRET],
            cuid=entry.options.get(CONF_CUID, DEFAULT_CUID),
        )
        domain_data[entry.entry_id] = client
    else:
        client.cuid = entry.options.get(CONF_CUID, DEFAULT_CUID)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
