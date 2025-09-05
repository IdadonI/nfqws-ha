"""Data coordinator for NFQWS HA integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import TypedDict
import re

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN, CONF_SSH_PORT, DEFAULT_SSH_PORT, CONF_STATUS_MONITORING, 
    CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, CONF_OPENWRT_MODE,
    CMD_STATUS_KEENETIC, CMD_STATUS_OPENWRT,
    CMD_START_KEENETIC, CMD_START_OPENWRT,
    CMD_STOP_KEENETIC, CMD_STOP_OPENWRT,
    CMD_RESTART_KEENETIC, CMD_RESTART_OPENWRT
)
from .ssh_helper import SSHHelper

_LOGGER = logging.getLogger(__name__)

class NFQWSData(TypedDict):
    """Data structure for NFQWS coordinator."""
    status: str
    available: bool
    is_running: bool
    nfqws_version: str
    manufacturer: str
    model: str

class NFQWSDataUpdateCoordinator(DataUpdateCoordinator[NFQWSData]):
    """Class to manage fetching NFQWS data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        # Use scan interval if status_monitoring is enabled, otherwise use very long interval
        update_interval = timedelta(seconds=3600)  # 1 hour by default
        
        if entry.data.get(CONF_STATUS_MONITORING, False):
            update_interval = timedelta(seconds=entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=update_interval,
        )
        self.entry = entry
        self.nfqws_version = "unknown"
        self.is_openwrt = entry.data.get(CONF_OPENWRT_MODE, False)
        
        # Set device info based on mode
        self.manufacturer = "OpenWRT" if self.is_openwrt else "Keenetic"
        self.model = "NFQWS"

    def _get_command(self, command_type: str) -> str:
        """Get the appropriate command based on platform."""
        if self.is_openwrt:
            commands = {
                "status": CMD_STATUS_OPENWRT,
                "start": CMD_START_OPENWRT,
                "stop": CMD_STOP_OPENWRT,
                "restart": CMD_RESTART_OPENWRT
            }
        else:
            commands = {
                "status": CMD_STATUS_KEENETIC,
                "start": CMD_START_KEENETIC,
                "stop": CMD_STOP_KEENETIC,
                "restart": CMD_RESTART_KEENETIC
            }
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
                "nfqws_version": self.nfqws_version,
                "manufacturer": self.manufacturer,
                "model": self.model
            }

    def _get_status(self) -> NFQWSData:
        """Get NFQWS status and version via SSH."""
        ssh_helper = SSHHelper(
            self.entry.data["host"],
            self.entry.data.get(CONF_SSH_PORT, DEFAULT_SSH_PORT),
            self.entry.data["username"],
            self.entry.data["password"]
        )
        
        try:
            if not ssh_helper.connect():
                self.logger.warning("Failed to connect to router")
                return {
                    "status": "connection_error", 
                    "available": False, 
                    "is_running": False,
                    "nfqws_version": self.nfqws_version,
                    "manufacturer": self.manufacturer,
                    "model": self.model
                }
            
            # Get NFQWS status
            status_cmd = self._get_command("status")
            stdout, stderr = ssh_helper.execute_command(status_cmd)
            
            if stderr:
                self.logger.warning("Error getting NFQWS status: %s", stderr)
            
            # Different status detection for OpenWRT vs Keenetic
            if self.is_openwrt:
                is_running = "running" in stdout.lower() if stdout else False
            else:
                is_running = "is running" in stdout if stdout else False
                
            status = "running" if is_running else "stopped"
            
            # Get NFQWS version (only once or if not set)
            if self.nfqws_version == "unknown":
                stdout_version, stderr_version = ssh_helper.execute_command("opkg info nfqws-keenetic")
                if stdout_version:
                    # Extract version from the output
                    version_match = re.search(r'Version:\s*([\d.]+)', stdout_version)
                    if version_match:
                        self.nfqws_version = version_match.group(1)
                    else:
                        self.logger.warning("Could not extract version from opkg output")
                elif stderr_version:
                    self.logger.warning("Error getting NFQWS version: %s", stderr_version)
            
            return {
                "status": status, 
                "available": True, 
                "is_running": is_running,
                "nfqws_version": self.nfqws_version,
                "manufacturer": self.manufacturer,
                "model": self.model
            }
                
        except Exception as err:
            self.logger.error("Unexpected error: %s", err)
            return {
                "status": "error", 
                "available": False, 
                "is_running": False,
                "nfqws_version": self.nfqws_version,
                "manufacturer": self.manufacturer,
                "model": self.model
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
        
        command = self._get_command(command_type)
        if not command:
            self.logger.error("Unknown command type: %s", command_type)
            return False
        
        try:
            stdout, stderr = await self.hass.async_add_executor_job(
                ssh_helper.execute_command, command, 30
            )
            
            if stderr:
                self.logger.error("Error executing command %s: %s", command, stderr)
                return False
            return True
            
        except Exception as err:
            self.logger.error("Error executing command: %s", err)
            return False
        finally:
            ssh_helper.disconnect()