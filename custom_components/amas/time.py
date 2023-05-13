"""Support for AMASTech Sensors."""
from __future__ import annotations

import logging
from typing import Any
from datetime import time, datetime


from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME

from homeassistant.components.time import TimeEntity
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
    AMASTimeEntityDescription
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


class AMASNumber(AMASTechEntity, TimeEntity):
    """Representation of a AMAS light number."""

    entity_description: AMASTimeEntityDescription

    def __init__(
        self,
        api: AMASHub,
        coordinator: DataUpdateCoordinator,
        _name: str,
        _device_unique_id: str,
        description: AMASTimeEntityDescription,
    ) -> None:
        """Initialize a AMAS sensor."""
        super().__init__(api, coordinator, _name, _device_unique_id)
        self.entity_description = description

        self._attr_name = f"{_name} {description.name}"
        self._attr_unique_id = f"{self._device_unique_id}/{description.name}"

    @property
    def native_value(self) -> Any:
        """Return the state of the device."""
        act_key = str(self.entity_description.key).split('_')[1]
        utc_aware = datetime.utcnow().astimezone(datetime.utcnow().astimezone().tzinfo)
        local_aware = datetime.now().astimezone()
        time_delta = local_aware - utc_aware
        time_delta = time_delta.days*24*3600 + time_delta.seconds
        time_delta_min = int(time_delta/60)
        delta_min = time_delta_min%60
        delta_hour = time_delta_min//60
        native = str(self.api.device_info['light'][act_key])
        _LOGGER.debug("Got UTC value light control " + act_key + ': ' + native)
        native_hour = native[0]+native[1]
        native_min = native[2]+native[3]
        converted_min = int(int(native_min) + delta_min)
        if converted_min >= 60:
            converted_hour = int(1 + delta_hour + int(native_hour))
            converted_min = int(converted_min%60)
        elif converted_min < 60 and converted_min >= 0:
            converted_hour = int(delta_hour + int(native_hour))
        if converted_hour < 0:
            converted_hour = int(converted_hour + 24)
        elif converted_hour >= 24:
            converted_hour = int(converted_hour - 24)
        converted_min = str(converted_min) if len(str(converted_min)) == 2 else '0' + str(converted_min)
        converted_hour = str(converted_hour) if len(str(converted_hour)) == 2 else '0' + str(converted_hour)
        return time(converted_hour, converted_min)

    async def async_set_native_value(self, value: time) -> None:
        """Update the current value."""
        try:
            act_key = str(self.entity_description.key).split('_')[1]
            _LOGGER.debug("Got local value light control " + act_key + ': ' + value.isoformat())
            utc_aware = datetime.utcnow().astimezone(datetime.utcnow().astimezone().tzinfo)
            local_aware = datetime.now().astimezone()
            time_delta = utc_aware - local_aware
            time_delta = time_delta.days*24*3600 + time_delta.seconds
            time_delta_min = int(time_delta/60)
            delta_min = time_delta_min%60
            delta_hour = time_delta_min//60
            native = value.isoformat()
            native_hour = native.split(':')[0]
            native_min = native.split(':')[1]
            converted_min = int(int(native_min) + delta_min)
            if converted_min >= 60:
                converted_hour = int(1 + delta_hour + int(native_hour))
                converted_min = int(converted_min%60)
            elif converted_min < 60 and converted_min >= 0:
                converted_hour = int(delta_hour + int(native_hour))
            if converted_hour < 0:
                converted_hour = int(converted_hour + 24)
            elif converted_hour >= 24:
                converted_hour = int(converted_hour - 24)
            if converted_min == 59:
                converted_min = 0
                if converted_hour < 24:
                    converted_hour = converted_hour + 1
                else:
                    converted_hour = 0
            if converted_min == 29 or converted_min == 14 or converted_min == 44 or converted_min == 4 or converted_min == 9 or converted_min == 19 or converted_min == 24 or converted_min == 34 or converted_min == 39 or converted_min == 49 or converted_min == 54:
                converted_min = converted_min + 1
            converted_min = str(converted_min) if len(str(converted_min)) == 2 else '0' + str(converted_min)
            converted_hour = str(converted_hour) if len(str(converted_hour)) == 2 else '0' + str(converted_hour)
            military = converted_hour + converted_min
            if military == '2400': military = '0000'
            _LOGGER.debug("Sending light control " + act_key + ': ' + military)
            await self.api.control_device({'light': {act_key: military, 'override': False}})
        except Exception as err:
            _LOGGER.error("Unable to turn on light control " + act_key + " : %s", err)
        
