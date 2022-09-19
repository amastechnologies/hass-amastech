import json
import string
import requests, logging
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from homeassistant.components.switch import (SwitchEntity, PLATFORM_SCHEMA)
from homeassistant.const import (CONF_HOST, CONF_API_KEY)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
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

    for i in [AMASCirculationEntity, AMASDrainEntity]:
        async_add_entities(i(coordinator, hub))

class AMASCirculationEntity(CoordinatorEntity[AMASDataCoordinator], SwitchEntity):
    """AMAS Circulatory Pump CoordinatorEntity.

    The CoordinatorEntity class provides:
      should_poll
      async_update
      async_added_to_hass
      available

    """

    def __init__(self, coordinator, hub):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self._attr_name = 'Circulation'
        self.hub = hub

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self.coordinator.data["pump"]["powered"]
        self._attr_unique_id = 'AMAS-' + str(self.coordinator.data["dev_id"]) + '-CP.CYCLE'
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        """Turn the circulation on.

        Example method how to request data updates.
        """
        response = self.hub.control_device({'pump': {'powered': True}})

        # Update the data
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the circulation on.

        Example method how to request data updates.
        """
        response = self.hub.control_device({'pump': {'powered': False}})

        # Update the data
        await self.coordinator.async_request_refresh()

class AMASDrainEntity(CoordinatorEntity[AMASDataCoordinator], SwitchEntity):
    """AMAS Drain Pump CoordinatorEntity.

    The CoordinatorEntity class provides:
      should_poll
      async_update
      async_added_to_hass
      available

    """

    def __init__(self, coordinator, hub):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self._attr_name = 'Drain'
        self.hub = hub

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on = self.coordinator.data["pump"]["drain"]
        self._attr_unique_id = 'AMAS-' + str(self.coordinator.data["dev_id"]) + '-CP.DRAIN'
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        """Turn the circulation on.

        Example method how to request data updates.
        """
        response = self.hub.control_device({'pump': {'drain': True}})

        # Update the data
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn the circulation on.

        Example method how to request data updates.
        """
        response = self.hub.control_device({'pump': {'drain': False}})

        # Update the data
        await self.coordinator.async_request_refresh()