"""Data coordinator for NFQWS HA integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import TypedDict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN, CONF_SSH_PORT, DEFAULT_SSH_PORT, CONF_STATUS_MONITORING, 
    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, CONF_OPENWRT_MODE,
    CONF_USE_OLD_VERSION,
    CMD_STATUS_KEENETIC, CMD_STATUS_OPENWRT,
    CMD_START_KEENETIC, CMD_START_OPENWRT,
    CMD_STOP_KEENETIC, CMD_STOP_OPENWRT,
    CMD_RESTART_KEENETIC, CMD_RESTART_OPENWRT,
    CMD_STATUS_KEENETIC_V2, CMD_START_KEENETIC_V2,
    CMD_STOP_KEENETIC_V2, CMD_RESTART_KEENETIC_V2
)
from .ssh_helper import SSHHelper

_LOGGER = logging.getLogger(__name__)

class NFQWSData(TypedDict):
    """Data structure for NFQWS coordinator."""
    status: str
    available: bool
    is_running: bool
    manufacturer: str
    model: str

class NFQWSDataUpdateCoordinator(DataUpdateCoordinator[NFQWSData]):
    """Class to manage fetching NFQWS data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        update_interval = timedelta(seconds=3600)
        if entry.data.get(CONF_STATUS_MONITORING, False):
            update_interval = timedelta(seconds=entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=update_interval,
        )
        self.entry = entry
        self.is_openwrt = entry.data.get(CONF_OPENWRT_MODE, False)
        self.use_old_version = entry.data.get(CONF_USE_OLD_VERSION, False)
        
        self.manufacturer = "OpenWRT" if self.is_openwrt else "Keenetic"
        self.model = "NFQWS2" if not self.use_old_version and not self.is_openwrt else "NFQWS"

    def _get_command(self, command_type: str) -> str:
        """Get the appropriate command based on platform and version."""
        if self.is_openwrt:
            commands = {
                "status": CMD_STATUS_OPENWRT,
                "start": CMD_START_OPENWRT,
                "stop": CMD_STOP_OPENWRT,
                "restart": CMD_RESTART_OPENWRT
            }
        else:
            if self.use_old_version:
                commands = {"status": CMD_STATUS_KEENETIC, "start": CMD_START_KEENETIC, "stop": CMD_STOP_KEENETIC, "restart": CMD_RESTART_KEENETIC}
            else:
                commands = {"status": CMD_STATUS_KEENETIC_V2, "start": CMD_START_KEENETIC_V2, "stop": CMD_STOP_KEENETIC_V2, "restart": CMD_RESTART_KEENETIC_V2}
        return commands.get(command_type, "")

    async def _async_update_data(self) -> NFQWSData:
        """Fetch data from router via SSH."""
        try:
            return await self.hass.async_add_executor_job(self._get_status)
        except Exception as err:
            self.logger.error("Error fetching NFQWS status: %s", err)
            return {
                "status": "error", 
                "available": False, 
                "is_running": False,
                "manufacturer": self.manufacturer,
                "model": self.model
            }

    def _get_status(self) -> NFQWSData:
        """Get NFQWS status via SSH."""
        ssh_helper = SSHHelper(
            self.entry.data["host"],
            self.entry.data.get(CONF_SSH_PORT, DEFAULT_SSH_PORT),
            self.entry.data["username"],
            self.entry.data["password"]
        )
        
        try:
            if not ssh_helper.connect():
                return {
                    "status": "connection_error", 
                    "available": False, 
                    "is_running": False,
                    "manufacturer": self.manufacturer,
                    "model": self.model
                }
            
            stdout, _ = ssh_helper.execute_command(self._get_command("status"))
            is_running = bool(stdout and "running" in stdout.lower())
            
            return {
                "status": "running" if is_running else "stopped", 
                "available": True, 
                "is_running": is_running,
                "manufacturer": self.manufacturer,
                "model": self.model
            }
                
        except Exception as err:
            self.logger.error("Unexpected error in coordinator: %s", err)
            return {
                "status": "error", "available": False, "is_running": False,
                "manufacturer": self.manufacturer, "model": self.model
            }
        finally:
            ssh_helper.disconnect()

    async def async_execute_command(self, command_type: str) -> bool:
        """Execute a command via SSH."""
        ssh_helper = SSHHelper(
            self.entry.data["host"],
            self.entry.data.get(CONF_SSH_PORT, DEFAULT_SSH_PORT),
            self.entry.data["username"],
            self.entry.data["password"]
        )
        try:
            await self.hass.async_add_executor_job(ssh_helper.connect)
            await self.hass.async_add_executor_job(ssh_helper.execute_command, self._get_command(command_type), 30)
            return True
        except Exception as err:
            self.logger.error("Error executing command: %s", err)
            return False
        finally:
            ssh_helper.disconnect()