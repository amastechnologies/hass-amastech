"""Support for AMASTech Sensors."""
from __future__ import annotations

import logging
from typing import Any
import datetime


from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConditionError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator


from .const import (
    DOMAIN as AMAS_DOMAIN,
    DATA_KEY_API,
    DATA_KEY_COORDINATOR,
    NUMBER_TYPES,
    AMASHub,
    AMASNumberEntityDescription
    )
from . import AMASTechEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up AMAS Tech Sensors."""
    name = entry.data[CONF_NAME]
    amas_data = hass.data[AMAS_DOMAIN][entry.entry_id]
    numbers = [
        AMASNumber(
            amas_data[DATA_KEY_API],
            amas_data[DATA_KEY_COORDINATOR],
            name,
            entry.entry_id,
            description,
        )
        for description in NUMBER_TYPES
    ]
    async_add_entities(numbers, True)


class AMASNumber(AMASTechEntity, NumberEntity):
    """Representation of a AMAS light number."""

    entity_description: AMASNumberEntityDescription

    def __init__(
        self,
        api: AMASHub,
        coordinator: DataUpdateCoordinator,
        _name: str,
        _device_unique_id: str,
        description: AMASNumberEntityDescription,
    ) -> None:
        """Initialize a AMAS sensor."""
        super().__init__(api, coordinator, _name, _device_unique_id)
        self.entity_description = description

        self._attr_name = f"{_name} {description.name}"
        self._attr_unique_id = f"{self._device_unique_id}/{description.name}"
        self._attr_mode = NumberMode.BOX

    @property
    def native_value(self) -> Any:
        """Return the state of the device."""
        act_key = str(self.entity_description.key).split('_')
        value = self.api.device_info[act_key[0]][act_key[1]]
            
        _LOGGER.debug("Got " + act_key[0] + " value " + act_key[1] + ': ' + str(value))
        
        return value
        

    async def async_set_native_value(self, value: int) -> None:
        """Update the current value."""
        act_key = str(self.entity_description.key).split('_')
        value = int(float(value))
        _LOGGER.debug("Got pump control " + act_key[1] + ': ' + str(value))
        await self.api.control_device({act_key[0]: {act_key[1]: value}})
        
