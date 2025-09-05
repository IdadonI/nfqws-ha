"""The NFQWS HA integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, CONF_SSH_PORT, DEFAULT_SSH_PORT, CONF_STATUS_MONITORING
from .coordinator import NFQWSDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Важен порядок: сначала сенсоры, потом кнопки
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up NFQWS HA from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Create coordinator
    coordinator = NFQWSDataUpdateCoordinator(hass, entry)
    
    try:
        # Try to get initial data (including nfqws version)
        await coordinator.async_refresh()
        
        # Don't fail setup if connection is temporarily unavailable
        if not coordinator.data["available"]:
            _LOGGER.warning(
                "Initial connection to router failed, but integration will continue trying. "
                "Check your SSH credentials and network connectivity."
            )
            
    except Exception as err:
        _LOGGER.error("Error setting up NFQWS HA integration: %s", err)
        raise ConfigEntryNotReady from err

    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Setup platforms (сенсоры будут созданы первыми)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok and entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)