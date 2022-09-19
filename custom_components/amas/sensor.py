"""Support for AMASTech Sensors."""
from __future__ import annotations

import logging
import json
import string
import requests

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
import voluptuous as vol

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription, SensorStateClass, SensorDeviceClass
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.const import TEMP_CELSIUS, PERCENTAGE
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

    for i in [AMASTempSensor, AMASHumidSensor, AMASWaterSensor]:
        async_add_entities(i(coordinator))

class AMASTempSensor(CoordinatorEntity[AMASDataCoordinator], SensorEntity):
    """AMAS Ambient Temperature Sensor CoordinatorEntity.

    The CoordinatorEntity class provides:
      should_poll
      async_update
      async_added_to_hass
      available

    """
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Ambient Temperature"
        self._attr_native_unit_of_measurement = TEMP_CELSIUS
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.coordinator.data['sensors']['ambient_temp']
        self._attr_unique_id = 'AMAS-' + str(self.coordinator.data["dev_id"]) + '-SHT.TEMP'
        self.async_write_ha_state()

class AMASHumidSensor(CoordinatorEntity[AMASDataCoordinator], SensorEntity):
    """AMAS Ambient Humidity Sensor CoordinatorEntity.

    The CoordinatorEntity class provides:
      should_poll
      async_update
      async_added_to_hass
      available

    """
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Ambient Humidity"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_device_class = SensorDeviceClass.HUMIDITY
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.coordinator.data['sensors']['humidity']
        self._attr_unique_id = 'AMAS-' + str(self.coordinator.data["dev_id"]) + '-SHT.HUMID'
        self.async_write_ha_state()

class AMASWaterSensor(CoordinatorEntity[AMASDataCoordinator], SensorEntity):
    """AMAS Ambient Water Level Sensor CoordinatorEntity.

    The CoordinatorEntity class provides:
      should_poll
      async_update
      async_added_to_hass
      available

    """
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "Water Level"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.coordinator.data['sensors']['water_level']/4500*100
        self._attr_unique_id = 'AMAS-' + str(self.coordinator.data["dev_id"]) + '-WS'
        self.async_write_ha_state()
