"""The AMASTech integration."""
from __future__ import annotations
import logging


import async_timeout
import voluptuous as vol
import asyncio
from datetime import datetime

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_API_TOKEN,
    CONF_HOST,
    CONF_NAME,
    Platform,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession
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
            vol.Required(CONF_ACCESS_TOKEN): cv.string,
            vol.Required(CONF_API_TOKEN): cv.string,
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
    api_key = entry.data[CONF_ACCESS_TOKEN]
    name = entry.data[CONF_NAME]
    mactoken = entry.data[CONF_API_TOKEN]
    api = AMASHub(host, hass, async_create_clientsession(hass))
    if await api.authenticate(api_key, mactoken):
        hass.config_entries.async_update_entry(entry, unique_id=('AMAS-'+str(api.device_info['dev_id'])))
    else: raise ConfigEntryAuthFailed
    
    # TODO 3. Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)
    
    async def async_update_data() -> None:
        """Fetch data from API endpoint.

        """
        if api.stream_task is None:
            api.stream_task = asyncio.create_task(api.stream_info())
        now = datetime.now().strftime('%s')
        last_update = api.last_update
        if now - last_update > 180:
            if await api.check_connection():
                try:
                    api.stream_task.cancel()
                except: pass
                await asyncio.sleep(5)
                api.stream_task = asyncio.create_task(api.stream_info())
            else:
                raise ConfigEntryNotReady


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
    platforms = [Platform.SWITCH, Platform.SENSOR, Platform.BINARY_SENSOR, Platform.TIME, Platform.NUMBER]
    return platforms


class AMASTechEntity(CoordinatorEntity):
    """Representation of a AMASTech entity."""

    def __init__(
        self,
        api: AMASHub,
        coordinator: DataUpdateCoordinator,
        _name: str,
        _device_unique_id: str,
    ) -> None:
        """Initialize a AMASTech entity."""
        super().__init__(coordinator)
        self.api = api
        self._name = _name
        self._device_unique_id = _device_unique_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information of the entity."""
        config_url = f"http://{self.api.host}/configure"
        
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_unique_id)},
            name=self._name,
            manufacturer="AMAS Technologies LLC",
            configuration_url=config_url,
        )
