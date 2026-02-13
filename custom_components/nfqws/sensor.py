"""Sensor platform for NFQWS HA."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import NFQWSDataUpdateCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: NFQWSDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([NFQWSSensor(coordinator, entry)])

class NFQWSSensor(CoordinatorEntity[NFQWSDataUpdateCoordinator], SensorEntity):
    """Representation of an NFQWS Status Sensor."""

    def __init__(self, coordinator: NFQWSDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_has_entity_name = True
        self._attr_translation_key = "nfqws_status" 

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        return self.coordinator.data.get("status")

    @property
    def icon(self) -> str:
        """Return the icon based on status."""
        if self.coordinator.data.get("is_running"):
            return "mdi:check-network"
        return "mdi:close-network"

    @property
    def device_info(self):
        """Return device information to link with buttons."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
        }
