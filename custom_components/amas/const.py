"""Constants for the AMASTech integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
import json, logging
import aiohttp
import async_timeout
from datetime import timedelta
from typing import Any
from homeassistant.components.sensor import SensorEntityDescription, SensorDeviceClass
from homeassistant.components.number import NumberEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntityDescription,
)
from homeassistant.const import TEMP_CELSIUS, PERCENTAGE
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
import os
from binascii import a2b_base64, b2a_base64
from json import loads, dumps

_LOGGER = logging.getLogger(__name__)


DOMAIN = 'amas'
DEFAULT_NAME = 'AMAS'
DATA_KEY_API = 'api'
DATA_KEY_COORDINATOR = 'coordinator'
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)


def decrypt(payload, token):
     enc = a2b_base64(payload)
     IV = enc[:16]
     message = enc[16:]
     hmm = Cipher(algorithms.AES(token), modes.CBC(IV))
     decryptor = hmm.decryptor()
     data = decryptor.update(message) + decryptor.finalize()
     data = bytes((x for x in data if x >= 0x20 and x < 127))
     data = data.decode()
     return data

def encrypt(data, token):
    padder = padding.PKCS7(128).padder()
    data = padder.update(data) + padder.finalize()
    IV = os.urandom(16)
    cipher = Cipher(algorithms.AES(token), modes.CBC(IV))
    encryptor = cipher.encryptor()
    ct = encryptor.update(data) + encryptor.finalize()
    enc = IV + ct
    enc = b2a_base64(enc).decode()
    enc = enc.replace('\n','=')
    return enc


class AMASHub:
    """AMASHub class to check authentication and get device info.

    """

    def __init__(self, host: str, hass: HomeAssistant, session: aiohttp.ClientSession) -> None:
        """Initialize."""
        self.host = host
        self.session = session
        self.hass = hass
        self.loop = hass.loop
        self.api_key = ''
        self.device_info = {}

    async def authenticate(self, api_key: str) -> bool:
        """Test if we can decrypt responses."""
        url = 'http://' + self.host + '/alerts'
        headers = {'Accept': '*/*'}
        try:
            api_key = a2b_base64(api_key)
            # r = requests.get(url, headers=headers)
            async with async_timeout.timeout(10):
                response = await self.session.get(url, headers=headers)
            if response.status == 200:
                payload = await response.text()
                _LOGGER.debug("Reponse content: %s", payload)
                alerts_dic = loads(decrypt(payload, api_key))
                self.api_key = api_key
                return True
            else:
                return False
        except Exception as e:
            _LOGGER.warning("Failed to connect: %s", e)
            raise ConfigEntryNotReady
    
    async def get_data(self) -> json:
        """Get device information."""
        url = 'http://' + self.host + '/data'
        headers = {'Accept': '*/*'}
        try:
            # r = requests.get(url, headers=headers)
            async with async_timeout.timeout(10):
                response = await self.session.get(url, headers=headers)
                _LOGGER.debug("Reponse content: %s", str(response.content))
            if response.status == 200:
                device_info = await response.text()
                _LOGGER.debug("Reponse content: %s", device_info)
                try:
                    device_info = loads(decrypt(device_info, self.api_key))
                except: raise ConfigEntryAuthFailed
                device_info = device_info['state']['reported']
                _LOGGER.debug("Device info: %s", str(device_info))
                self.device_info.update(device_info)
                return device_info
            else:
                _LOGGER.critical("Status code: "+str(response.status))
                raise ConfigEntryNotReady
        except Exception as e:
            _LOGGER.warning("Failed to connect: %s", e)
            raise ConfigEntryNotReady
    
    async def get_alerts(self) -> json:
        """Get device alerts."""
        url = 'http://' + self.host + '/alerts'
        headers = {'Accept': '*/*'}
        try:
            # r = requests.get(url, headers=headers)
            async with async_timeout.timeout(10):
                response = await self.session.get(url, headers=headers)
                _LOGGER.info("Reponse content: %s", str(response.content))
            if response.status == 200:
                device_info = await response.text()
                _LOGGER.debug("Reponse content: %s", device_info)
                try:
                    device_info = loads(decrypt(device_info, self.api_key))
                except: raise ConfigEntryAuthFailed
                device_info = device_info['state']['reported']
                _LOGGER.debug("Device info: %s", str(device_info))
                return device_info
            else:
                _LOGGER.critical("Status code: "+str(response.status))
                raise ConfigEntryNotReady
        except Exception as e:
            _LOGGER.warning("Failed to connect: %s", e)
            raise ConfigEntryNotReady

    async def control_device(self, state: dict[str, Any]) -> None:
        """Control device."""
        url = 'http://' + self.host + '/configure'
        headers = {'Accept': '*/*'}
        body = {'state': {'desired': state}}
        payload = encrypt(dumps(body).encode(), self.api_key).encode()
        try:
            # r = requests.post(url, headers=headers, body=body)
            async with async_timeout.timeout(10):
                response = await self.session.post(url, data=payload, headers=headers)
                _LOGGER.debug("Response content: %s", str(response.content))
            if response.status == 200:
                device_info = await response.text()
                _LOGGER.debug("Reponse content: %s", device_info)
                try:
                    device_info = loads(decrypt(device_info, self.api_key))
                except: raise ConfigEntryAuthFailed
                device_info = device_info['state']['reported']
                self.device_info = device_info
                _LOGGER.debug("Device info: %s", str(response.content))
            else:
                _LOGGER.critical("Status code: "+str(response.status))
                raise ConfigEntryNotReady
        except Exception as e:
            _LOGGER.warning("Failed to connect: %s", e)
            raise ConfigEntryNotReady

    async def update_info(self) -> None:
        """Update device information."""
        url = 'http://' + self.host + '/data'
        headers = {'Accept': '*/*'}
        try:
            # r = requests.get(url, headers=headers)
            async with async_timeout.timeout(10):
                response = await self.session.get(url, headers=headers)
                _LOGGER.debug("Reponse content: %s", str(response.content))
            if response.status == 200:
                device_info = await response.text()
                try:
                    device_info = loads(decrypt(device_info, self.api_key))
                except: raise ConfigEntryAuthFailed
                device_info = device_info['state']['reported']
                _LOGGER.debug("Device info: %s", str(device_info))
            else:
                _LOGGER.critical("Status code: "+str(response.status))
                raise ConfigEntryNotReady
            url = 'http://' + self.host + '/alerts'
            # r = requests.get(url, headers=headers)
            async with async_timeout.timeout(10):
                response = await self.session.get(url, headers=headers)
                _LOGGER.debug("Resonse content: %s", str(response.content))
            if response.status == 200:
                device_alerts = await response.text()
                try:
                    device_alerts = loads(decrypt(device_alerts, self.api_key))
                except: raise ConfigEntryAuthFailed
                device_alerts = device_alerts['state']['reported']
                _LOGGER.debug("Device alerts: %s", str(device_alerts))
            else:
                _LOGGER.critical("Status code: "+str(response.status))
                raise ConfigEntryNotReady
            device_info.update(device_alerts)
            self.device_info = device_info
        except Exception as e:
            _LOGGER.warning("Failed to connect: %s", e)
            raise ConfigEntryNotReady

@dataclass
class AMASNumberEntityDescription(NumberEntityDescription):
    """Describes AMASTech number entity."""

    icon: str = "mdi:leaf"


NUMBER_TYPES: tuple[AMASNumberEntityDescription, ...] = (
    AMASNumberEntityDescription(
        key="light_on",
        name="Light On",
        icon="mdi:lightbulb-on",
        native_max_value=2400,
        native_min_value=0,
    ),
    AMASNumberEntityDescription(
        key="light_off",
        name="Light Off",
        icon="mdi:lightbulb-off-outline",
        native_max_value=2400,
        native_min_value=0,
    ),
)


@dataclass
class AMASSensorEntityDescription(SensorEntityDescription):
    """Describes AMASTech sensor entity."""

    icon: str = "mdi:leaf"


SENSOR_TYPES: tuple[AMASSensorEntityDescription, ...] = (
    AMASSensorEntityDescription(
        key="ambient_temp",
        name="Ambient Temperature",
        native_unit_of_measurement=TEMP_CELSIUS,
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    AMASSensorEntityDescription(
        key="humidity",
        name="Relative Humidity",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:water-percent",
        device_class=SensorDeviceClass.HUMIDITY,
    ),
    AMASSensorEntityDescription(
        key="water_level",
        name="Water Level",
        native_unit_of_measurement=PERCENTAGE,
        icon="mdi:waves-arrow-up",
    ),
)


@dataclass
class RequiredAMASBinaryDescription:
    """Represent the required attributes of the AMASTech binary description."""

    state_value: Callable[[AMASHub], bool]


@dataclass
class AMASBinarySensorEntityDescription(
    BinarySensorEntityDescription, RequiredAMASBinaryDescription
):
    """Describes AMASTech binary sensor entity."""

    extra_value: Callable[[AMASHub], dict[str, Any] | None] = lambda api: None


BINARY_SENSOR_TYPES: tuple[AMASBinarySensorEntityDescription, ...] = (
    AMASBinarySensorEntityDescription(
        key="light_status",
        name="Light Status",
        entity_registry_enabled_default=True,
        device_class=BinarySensorDeviceClass.LIGHT,
        state_value=lambda api: bool(api.device_info['light']['status']),
    ),
    AMASBinarySensorEntityDescription(
        key="pump_status",
        name="Pump Status",
        entity_registry_enabled_default=True,
        device_class=BinarySensorDeviceClass.RUNNING,
        state_value=lambda api: bool(api.device_info['pump']['status']),
    ),
    AMASBinarySensorEntityDescription(
        key="water_alert",
        name="Water Alert",
        entity_registry_enabled_default=False,
        device_class=BinarySensorDeviceClass.BATTERY,
        state_value=lambda api: api.device_info['water_level_alert'] == 'Low',
    ),
    AMASBinarySensorEntityDescription(
        key="temp_alert",
        name="Temperature Alert",
        entity_registry_enabled_default=False,
        device_class=BinarySensorDeviceClass.PROBLEM,
        state_value=lambda api: api.device_info['temp_alert'] == 'Low' or api.device_info['temp_alert'] == 'High',
    ),
    AMASBinarySensorEntityDescription(
        key="humidity_alert",
        name="Humidity Alert",
        entity_registry_enabled_default=False,
        device_class=BinarySensorDeviceClass.PROBLEM,
        state_value=lambda api: api.device_info['humidity_alert'] == 'Low' or api.device_info['humidity_alert'] == 'High',
    ),
)


