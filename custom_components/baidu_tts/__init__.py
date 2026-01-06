"""Baidu TTS integration for Home Assistant."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.TTS]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Baidu TTS from a config entry."""
    _LOGGER.info("Setting up Baidu TTS entry: %s", entry.entry_id)
    
    # 设置TTS平台
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # 设置更新监听器
    entry.async_on_unload(entry.add_update_listener(options_update_listener))
    
    return True

async def options_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.info("Baidu TTS options updated, reloading entry")
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading Baidu TTS entry: %s", entry.entry_id)
    
    # 卸载平台
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    # 清理数据
    if unload_ok and DOMAIN in hass.data:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    
    return unload_ok
