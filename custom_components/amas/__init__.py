"""The AMASTech integration."""
from __future__ import annotations
from datetime import timedelta
import logging

import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ConfigEntryAuthFailed 
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)


from .const import DOMAIN
import requests, json
from . import config_flow

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.SWITCH, Platform.SENSOR, Platform.BINARY_SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AMASTech from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    host = entry.data['CONF_HOST']
    api_key = entry.data['CONF_API_KEY']
    hub = AMASHub(host)
    if await hub.authenticate(api_key):
        device_info = hub.get_data()
        hass.config_entries.async_update_entry(entry, unique_id='AMAS-'+str(device_info['dev_id']))
        hass.data[DOMAIN][entry.entry_id] = hub
    else:
        raise InvalidAuth
    # TODO 1. Create API instance
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)


    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

class AMASHub:
    """AMASHub class to check authentication and get device info.

    """

    def __init__(self, host: str) -> None:
        """Initialize."""
        self.host = host
        self.api_key = None

    async def authenticate(self, api_key: str) -> bool:
        """Test if we can authenticate with the host."""
        url = 'http://' + self.host + '/alerts'
        headers = {'User-Agent': 'hass', 'Accept': '*/*', 'x-api-key': api_key}
        try:
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                self.api_key = api_key
                return True
            else:
                return False
        except:
            raise CannotConnect
    
    def get_data(self) -> json:
        """Get device information."""
        url = 'http://' + self.host + '/data'
        headers = {'User-Agent': 'hass', 'Accept': '*/*', 'x-api-key': self.api_key}
        try:
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                device_info = json.loads(r.content.decode())['state']['reported']
                return device_info
            else:
                raise InvalidAuth
        except:
            raise CannotConnect
    
    def get_alerts(self) -> json:
        """Get device alerts."""
        url = 'http://' + self.host + '/alerts'
        headers = {'User-Agent': 'hass', 'Accept': '*/*', 'x-api-key': self.api_key}
        try:
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                device_alerts = json.loads(r.content.decode())['state']['reported']
                return device_alerts
            else:
                raise InvalidAuth
        except:
            raise CannotConnect

    def get_photo(self) -> requests:
        """Get device photo."""
        url = 'http://' + self.host + '/photo'
        headers = {'User-Agent': 'hass', 'Accept': '*/*', 'x-api-key': self.api_key}
        try:
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                return r
            else:
                raise InvalidAuth
        except:
            raise CannotConnect

    def control_device(self, state: json) -> json:
        """Control device."""
        url = 'http://' + self.host + '/configure'
        headers = {'User-Agent': 'hass', 'Accept': '*/*', 'x-api-key': self.api_key}
        body = {'state': {'desired': state}}
        try:
            r = requests.post(url, headers=headers, body=body)
            if r.status_code == 200:
                device_info = json.loads(r.content.decode())['state']['reported']
                return device_info
            else:
                raise InvalidAuth
        except:
            raise CannotConnect

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""

class AMASDataCoordinator(DataUpdateCoordinator):
    """AMAS Data coordinator."""

    def __init__(self, hass, hub):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="AMAS Data Coordinator",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=30),
        )
        self.hub = hub

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                device_info = self.hub.get_data()
                device_alerts = self.hub.get_alerts()
                device_info.update(device_alerts)
                return device_info
        except InvalidAuth as err:
            # Raising ConfigEntryAuthFailed will cancel future updates
            # and start a config flow with SOURCE_REAUTH (async_step_reauth)
            raise ConfigEntryAuthFailed from err
        except CannotConnect as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
