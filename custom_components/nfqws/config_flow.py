"""Config flow for NFQWS HA integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN, 
    CONF_SSH_PORT, 
    DEFAULT_SSH_PORT, 
    CONF_WEB_PORT, 
    DEFAULT_WEB_PORT, 
    CONF_STATUS_MONITORING, 
    DEFAULT_SCAN_INTERVAL, 
    CONF_OPENWRT_MODE,
    CONF_USE_OLD_VERSION
)
from .ssh_helper import SSHHelper

_LOGGER = logging.getLogger(__name__)

# Основная схема настройки
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_SSH_PORT, default=DEFAULT_SSH_PORT): cv.port,
        vol.Required(CONF_WEB_PORT, default=DEFAULT_WEB_PORT): cv.port,
        vol.Required(CONF_USERNAME, default="root"): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_OPENWRT_MODE, default=False): bool,
        # Новая опция: False по умолчанию означает использование nfqws2
        vol.Required(CONF_USE_OLD_VERSION, default=False): bool,
        vol.Required(CONF_STATUS_MONITORING, default=False): bool,
    }
)

STEP_STATUS_MONITORING_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=10, max=3600)
        ),
    }
)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    ssh_helper = SSHHelper(
        data[CONF_HOST],
        data[CONF_SSH_PORT],
        data[CONF_USERNAME],
        data[CONF_PASSWORD],
    )
    
    # Пытаемся подключиться в отдельном потоке, чтобы не блокировать HA
    result = await hass.async_add_executor_job(ssh_helper.connect)
    if not result:
        raise Exception("cannot_connect")
    
    ssh_helper.disconnect()
    return {"title": f"NFQWS - {data[CONF_HOST]}"}

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for NFQWS HA."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._user_input: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await validate_input(self.hass, user_input)
                self._user_input = user_input
                
                # Если включен мониторинг статуса, идем к следующему шагу настройки интервала
                if user_input[CONF_STATUS_MONITORING]:
                    return await self.async_step_status_monitoring()
                
                return self.async_create_entry(
                    title=f"NFQWS HA - {user_input[CONF_HOST]}", 
                    data=user_input
                )
            except Exception as err:
                _LOGGER.error("Connection validation failed: %s", err)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_status_monitoring(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the status monitoring configuration step (scan interval)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Объединяем данные из первого шага с интервалом сканирования
            data = {**self._user_input, **user_input}
            return self.async_create_entry(
                title=f"NFQWS HA - {data[CONF_HOST]}", 
                data=data
            )

        return self.async_show_form(
            step_id="status_monitoring",
            data_schema=STEP_STATUS_MONITORING_SCHEMA,
            errors=errors,
            description_placeholders={
                "host": self._user_input[CONF_HOST]
            }
        )