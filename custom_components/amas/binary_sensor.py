"""Support for AMASTech Sensors."""
from __future__ import annotations

import logging
import json
import string
import requests

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
import voluptuous as vol

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)


from .const import DOMAIN
from . import AMASDataCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Config entry example."""
    # assuming API object stored here by __init__.py
    hub = hass.data[DOMAIN][entry.entry_id]
    coordinator = AMASDataCoordinator(hass, hub)

    # Fetch initial data so we have data when entities subscribe
    #
    # If the refresh fails, async_config_entry_first_refresh will
    # raise ConfigEntryNotReady and setup will try again later
    #
    # If you do not want to retry setup on failure, use
    # coordinator.async_refresh() instead
    #
    await coordinator.async_config_entry_first_refresh()

    for i in [AMASPumpStatus, AMASLightStatus]:
        async_add_entities(i(coordinator))


class AMASPumpStatus(CoordinatorEntity[AMASDataCoordinator], BinarySensorEntity):
    """AMAS Pump Status CoordinatorEntity.

    The CoordinatorEntity class provides:
      should_poll
      async_update
      async_added_to_hass
      available

    """
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Pump Status"
        self._attr_device_class = BinarySensorDeviceClass.POWER

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self.coordinator.data['pump']['status']
        self._attr_unique_id = 'AMAS-' + str(self.coordinator.data["dev_id"]) + '-CP-STAT'
        self.async_write_ha_state()

class AMASLightStatus(CoordinatorEntity[AMASDataCoordinator], BinarySensorEntity):
    """AMAS Light Status CoordinatorEntity.

    The CoordinatorEntity class provides:
      should_poll
      async_update
      async_added_to_hass
      available

    """
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Light Status"
        self._attr_device_class = BinarySensorDeviceClass.POWER

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self.coordinator.data['light']['status']
        self._attr_unique_id = 'AMAS-' + str(self.coordinator.data["dev_id"]) + '-LT-STAT'
        self.async_write_ha_state()