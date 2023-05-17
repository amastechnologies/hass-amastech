from __future__ import annotations
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


from .const import (
    DOMAIN as AMAS_DOMAIN,
    DATA_KEY_API,
    DATA_KEY_COORDINATOR,
    )
from . import AMASTechEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up AMAS Tech switches."""
    name = entry.data[CONF_NAME]
    amas_data = hass.data[AMAS_DOMAIN][entry.entry_id]
    switches = [
        AMASCirculationSwitch(
            amas_data[DATA_KEY_API],
            amas_data[DATA_KEY_COORDINATOR],
            name+' Circulation',
            entry.entry_id,
        ),
        AMASDrainSwitch(
            amas_data[DATA_KEY_API],
            amas_data[DATA_KEY_COORDINATOR],
            name+' Drain',
            entry.entry_id,
        ),
        AMASLightOverrideSwitch(
            amas_data[DATA_KEY_API],
            amas_data[DATA_KEY_COORDINATOR],
            name+' Light Override',
            entry.entry_id,
        )
    ]
    async_add_entities(switches, True)


class AMASCirculationSwitch(AMASTechEntity, SwitchEntity):
    """Representation of a AMAS switch."""

    _attr_icon = "mdi:cached"

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique id of the switch."""
        return f"{self._device_unique_id}/Circulation"

    @property
    def is_on(self) -> bool:
        """Return if the service is on."""
        return bool(self.api.device_info["pump"]['powered'])  # type: ignore[no-any-return]

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the service."""
        try:
            _LOGGER.debug("Sending circulation on.")
            await self.api.control_device({'pump': {'powered': True}})
        except Exception as err:
            _LOGGER.error("Unable to turn on circulation: %s", err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the service."""
        try:
            _LOGGER.debug("Sending circulation off.")
            await self.api.control_device({'pump': {'powered': False}})
        except Exception as err:
            _LOGGER.error("Unable to turn off circulation: %s", err)

class AMASDrainSwitch(AMASTechEntity, SwitchEntity):
    """Representation of a AMAS switch."""

    _attr_icon = "mdi:water-minus"

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique id of the switch."""
        return f"{self._device_unique_id}/Drain"

    @property
    def is_on(self) -> bool:
        """Return if the service is on."""
        return bool(self.api.device_info["pump"]['drain'])  # type: ignore[no-any-return]

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the service."""
        try:
            _LOGGER.debug("Sending drain on.")
            await self.api.control_device({'pump': {'drain': True}})
        except Exception as err:
            _LOGGER.error("Unable to turn on drain: %s", err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the service."""
        try:
            _LOGGER.debug("Sending drain off.")
            await self.api.control_device({'pump': {'drain': False}})
        except Exception as err:
            _LOGGER.error("Unable to turn off drain: %s", err)

class AMASLightOverrideSwitch(AMASTechEntity, SwitchEntity):
    """Representation of a AMAS switch."""

    _attr_icon = "mdi:lightbulb-alert-outline"

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique id of the switch."""
        return f"{self._device_unique_id}/LightOverride"

    @property
    def is_on(self) -> bool:
        """Return if the service is on."""
        return bool(self.api.device_info['light']['status']) # type: ignore[no-any-return]

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the service."""
        try:
            _LOGGER.debug("Sending drain on.")
            await self.api.control_device({'light': {'override': '1'}})
        except Exception as err:
            _LOGGER.error("Unable to turn on light override: %s", err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the service."""
        try:
            _LOGGER.debug("Sending drain off.")
            await self.api.control_device({'light': {'override': '0'}})
        except Exception as err:
            _LOGGER.error("Unable to turn off light override: %s", err)
