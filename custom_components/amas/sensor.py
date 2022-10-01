"""Support for AMASTech Sensors."""
from __future__ import annotations

import logging
from typing import Any


from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator


from .const import (
    DOMAIN as AMAS_DOMAIN,
    DATA_KEY_API,
    DATA_KEY_COORDINATOR,
    SENSOR_TYPES,
    AMASHub,
    AMASSensorEntityDescription
    )
from . import AMASTechEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up AMAS Tech Sensors."""
    name = entry.data[CONF_NAME]
    amas_data = hass.data[AMAS_DOMAIN][entry.entry_id]
    sensors = [
        AMASSensor(
            amas_data[DATA_KEY_API],
            amas_data[DATA_KEY_COORDINATOR],
            name,
            entry.entry_id,
            description,
        )
        for description in SENSOR_TYPES
    ]
    async_add_entities(sensors, True)


class AMASSensor(AMASTechEntity, SensorEntity):
    """Representation of a Pi-hole sensor."""

    entity_description: AMASSensorEntityDescription

    def __init__(
        self,
        api: AMASHub,
        coordinator: DataUpdateCoordinator,
        _name: str,
        _device_unique_id: str,
        description: AMASSensorEntityDescription,
    ) -> None:
        """Initialize a AMAS sensor."""
        super().__init__(api, coordinator, _name, _device_unique_id)
        self.entity_description = description

        self._attr_name = f"{_name} {description.name}"
        self._attr_unique_id = f"{self._device_unique_id}/{description.name}"

    @property
    def native_value(self) -> Any:
        """Return the state of the device."""
        return round(self.api.device_info['sensors'][self.entity_description.key], 2)
        
