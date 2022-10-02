"""Support for AMASTech Sensors."""
from __future__ import annotations

import logging
from typing import Any
import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import CONF_NAME
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)


from .const import (
    DOMAIN as AMAS_DOMAIN,
    DATA_KEY_API,
    DATA_KEY_COORDINATOR,
    BINARY_SENSOR_TYPES,
    AMASHub,
    AMASBinarySensorEntityDescription
    )
from . import AMASTechEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the AMAS binary sensor."""
    name = entry.data[CONF_NAME]
    amas_data = hass.data[AMAS_DOMAIN][entry.entry_id]

    binary_sensors = [
        AMASBinarySensor(
            amas_data[DATA_KEY_API],
            amas_data[DATA_KEY_COORDINATOR],
            name,
            entry.entry_id,
            description,
        )
        for description in BINARY_SENSOR_TYPES
    ]

    async_add_entities(binary_sensors, True)


class AMASBinarySensor(AMASTechEntity, BinarySensorEntity):
    """Representation of a AMAS binary sensor."""

    entity_description: AMASBinarySensorEntityDescription

    def __init__(
        self,
        api: AMASHub,
        coordinator: DataUpdateCoordinator,
        _name: str,
        _device_unique_id: str,
        description: AMASBinarySensorEntityDescription,
    ) -> None:
        """Initialize a AMAS sensor."""
        super().__init__(api, coordinator, _name, _device_unique_id)
        self.entity_description = description
        self._attr_name = f"{_name} {description.name}"
        self._attr_unique_id = f"{self._device_unique_id}/{description.name}"

    @property
    def is_on(self) -> bool:
        """Return if the service is on."""

        return self.entity_description.state_value(self.api)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes of the Pi-hole."""
        return self.entity_description.extra_value(self.api)
