"""Sensor platform for NFQWS Keenetic."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, CONF_STATUS_MONITORING
from .coordinator import NFQWSDataUpdateCoordinator

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: NFQWSDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = []
    
    # Add status sensor only if status_monitoring is enabled (ПЕРВЫЙ!)
    if entry.data.get(CONF_STATUS_MONITORING, False):
        entities.append(NFQWSStatusSensor(coordinator, entry))
    
    # Always add NFQWS version sensor (ВТОРОЙ!)
    entities.append(NFQWSVersionSensor(coordinator, entry))
    
    async_add_entities(entities)

class NFQWSStatusSensor(SensorEntity):
    """Representation of NFQWS Status Sensor."""

    def __init__(self, coordinator: NFQWSDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._entry = entry
        
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_should_poll = False
        self._attr_has_entity_name = True

        # Set entity_id for better compatibility
        self.entity_id = f"sensor.nfqws_{entry.entry_id}_status"

    @property
    def translation_key(self) -> str:
        """Return the translation key for this entity."""
        return "nfqws_status_sensor"

    @property
    def icon(self) -> str:
        """Return the icon based on status."""
        if self.coordinator.data.get("status") == "running":
            return "mdi:cloud-check-outline"
        return "mdi:cloud-remove-outline"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        web_port = self._entry.data.get("web_port", 90)
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"{self.coordinator.data.get('manufacturer', 'Router')} - {self._entry.data['host']}",
            manufacturer=self.coordinator.data.get("manufacturer", "Unknown"),
            model=self.coordinator.data.get("model", "Router"),
            configuration_url=f"http://{self._entry.data['host']}:{web_port}/",
        )

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        return self.coordinator.data.get("status", "unknown")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.data.get("available", False)

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        return {
            "is_running": self.coordinator.data.get("is_running", False),
            "available": self.coordinator.data.get("available", False)
        }

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

class NFQWSVersionSensor(SensorEntity):
    """Representation of NFQWS Version Sensor."""

    def __init__(self, coordinator: NFQWSDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._entry = entry
        
        self._attr_unique_id = f"{entry.entry_id}_nfqws_version"
        self._attr_icon = "mdi:package-variant"
        self._attr_entity_registry_enabled_default = True
        self._attr_should_poll = False
        self._attr_has_entity_name = True

        # Set entity_id for better compatibility
        self.entity_id = f"sensor.nfqws_{entry.entry_id}_version"

    @property
    def translation_key(self) -> str:
        """Return the translation key for this entity."""
        return "nfqws_version_sensor"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        web_port = self._entry.data.get("web_port", 90)
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"{self.coordinator.data.get('manufacturer', 'Router')} - {self._entry.data['host']}",
            manufacturer=self.coordinator.data.get("manufacturer", "Unknown"),
            model=self.coordinator.data.get("model", "Router"),
            configuration_url=f"http://{self._entry.data['host']}:{web_port}/",
        )

    @property
    def native_value(self) -> str:
        """Return the NFQWS version."""
        return self.coordinator.data.get("nfqws_version", "unknown")

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        if self._entry.data.get(CONF_STATUS_MONITORING, False):
            self.async_on_remove(
                self.coordinator.async_add_listener(self.async_write_ha_state)
            )