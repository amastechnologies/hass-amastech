"""The AMASTech integration."""
from __future__ import annotations
from datetime import timedelta
import logging
import requests, json


import async_timeout
import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_NAME,
    Platform,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)


from .const import (
    DOMAIN, 
    DEFAULT_NAME, 
    AMASHub,
    DATA_KEY_API,
    DATA_KEY_COORDINATOR,
    MIN_TIME_BETWEEN_UPDATES
)

_LOGGER = logging.getLogger(__name__)

AMAS_SCHEMA = vol.Schema(
    vol.All(
        {
            vol.Required(CONF_HOST): cv.string,
            vol.Required(CONF_API_KEY): cv.string,
            vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        },
    )
)

CONFIG_SCHEMA = vol.Schema(
    vol.All(
        cv.deprecated(DOMAIN),
        {DOMAIN: vol.Schema(vol.All(cv.ensure_list, [AMAS_SCHEMA]))},
    ),
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the AMASTech integration."""

    hass.data[DOMAIN] = {}

    # import
    if DOMAIN in config:
        for conf in config[DOMAIN]:
            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN, context={"source": SOURCE_IMPORT}, data=conf
                )
            )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AMASTech from a config entry."""

    host = entry.data[CONF_HOST]
    api_key = entry.data[CONF_API_KEY]
    name = entry.data[CONF_NAME]
    api = AMASHub(host)
    if await api.authenticate(api_key):
        device_info = api.get_data()
        hass.config_entries.async_update_entry(entry, unique_id='AMAS-'+str(device_info['dev_id']))
    
    # TODO 3. Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)
    
    async def async_update_data() -> None:
        """Fetch data from API endpoint.

        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                await api.update_info()
                await api.update_photo()
        except ConfigEntryAuthFailed as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err
        except ConfigEntryNotReady as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=name,
        update_method=async_update_data,
        update_interval=MIN_TIME_BETWEEN_UPDATES,
    )

    hass.data[DOMAIN][entry.entry_id] = {
        DATA_KEY_API: api,
        DATA_KEY_COORDINATOR: coordinator,
        }

    await hass.config_entries.async_forward_entry_setups(entry, _async_platforms(entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, _async_platforms(entry)):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
@callback
def _async_platforms(entry: ConfigEntry) -> list[Platform]:
    """Return platforms to be loaded / unloaded."""
    platforms = [Platform.SWITCH, Platform.SENSOR, Platform.BINARY_SENSOR]
    return platforms


class AMASTechEntity(CoordinatorEntity):
    """Representation of a AMASTech entity."""

    def __init__(
        self,
        api: AMASHub,
        coordinator: DataUpdateCoordinator,
        name: str,
        device_unique_id: str,
    ) -> None:
        """Initialize a AMASTech entity."""
        super().__init__(coordinator)
        self.api = api
        self._name = name
        self._device_unique_id = device_unique_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information of the entity."""
        config_url = f"http://{self.api.host}/data"
        
        return DeviceInfo(
            identifiers={(DOMAIN, self.device_unique_id)},
            name=self._name,
            manufacturer="AMAS Technologies LLC",
            configuration_url=config_url,
        )
