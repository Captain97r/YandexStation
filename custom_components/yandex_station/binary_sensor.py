"""Support for Yandex Smart Home sensor."""
from __future__ import annotations

import logging
import string
import time
from typing import Any


from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.binary_sensor import BinarySensorEntityDescription
from homeassistant.components.binary_sensor import DEVICE_CLASS_MOTION

from . import CONF_INCLUDE
from . import DATA_CONFIG
from . import DOMAIN
from . import YandexQuasar

_LOGGER = logging.getLogger(__name__)

DEVICES = ["devices.types.sensor"]

SENSOR_TYPES: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="motion",
        name="Motion",
        device_class=DEVICE_CLASS_MOTION
    ),
)

TIMEOUT_SEC = 180


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensor from a config entry."""
    include = hass.data[DOMAIN][DATA_CONFIG][CONF_INCLUDE]
    quasar = hass.data[DOMAIN][entry.unique_id]

    devices = []
    for device in quasar.devices:
        if device["name"] in include and device["type"] in DEVICES:
            data = await quasar.get_device(device["id"])
            for prop in data["properties"]:
                for description in SENSOR_TYPES:
                    if prop["parameters"]["instance"] == description.key:
                        devices.append(
                            YandexBinarySensor(
                                quasar,
                                device,
                                prop["parameters"]["name"],
                                description,
                            )
                        )

    async_add_entities(devices, True)


# noinspection PyAbstractClass
class YandexBinarySensor(BinarySensorEntity):
    """Yandex Home sensor entity"""

    _motion = None

    def __init__(
            self,
            quasar: YandexQuasar,
            device: dict,
            name: str,
            description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize entity."""
        self.quasar = quasar
        self.device = device
        self.sensor_name = name
        self.entity_description = description

    @property
    def unique_id(self):
        """Return entity unique id."""
        return f"{self.device['id'].replace('-', '')}: {self.entity_description.name}"

    @property
    def name(self):
        """Return entity name."""
        return f"{self.device['name']}: {self.sensor_name}"

    @property
    def motion(self) -> string:
        """Return last motion event."""
        return self._motion

    async def async_update(self):
        """Update the entity."""
        data = await self.quasar.get_device(self.device["id"])

        for prop in data["properties"]:
            instance = prop["parameters"]["instance"]
            if instance == "motion":
                motion_last_updated = prop["last_updated"]
                time_now = time.time()
                if abs(time_now - float(motion_last_updated)) > TIMEOUT_SEC:
                    self._motion = "On"
                else:
                    self._motion = "Off"

    @property
    def native_value(self) -> Any:
        """Return the native value of the sensor."""
        return getattr(self, self.entity_description.key)
