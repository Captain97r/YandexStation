"""Support for Yandex Smart Home sensor."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import STATE_CLASS_MEASUREMENT
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.const import PERCENTAGE
from homeassistant.const import TEMP_CELSIUS
from homeassistant.const import PRESSURE_MMHG
from homeassistant.const import LIGHT_LUX

from . import CONF_INCLUDE
from . import DATA_CONFIG
from . import DOMAIN
from . import YandexQuasar

_LOGGER = logging.getLogger(__name__)

DEVICES = ["devices.types.humidifier", "devices.types.sensor"]

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="temperature",
        name="Temperature",
        native_unit_of_measurement=TEMP_CELSIUS,
        state_class=STATE_CLASS_MEASUREMENT,
    ),
    SensorEntityDescription(
        key="humidity",
        name="Humidity",
        native_unit_of_measurement=PERCENTAGE,
        state_class=STATE_CLASS_MEASUREMENT,
    ),
    SensorEntityDescription(
        key="pressure",
        name="Pressure",
        native_unit_of_measurement=PRESSURE_MMHG,
        state_class=STATE_CLASS_MEASUREMENT,
    ),
    SensorEntityDescription(
        key="illumination",
        name="Illumination",
        native_unit_of_measurement=LIGHT_LUX,
        state_class=STATE_CLASS_MEASUREMENT,
    ),
    SensorEntityDescription(
        key="motion",
        name="Motion",
        native_unit_of_measurement="",
        state_class=STATE_CLASS_MEASUREMENT,
    ),
)

SENSOR_KEYS: list[str] = [desc.key for desc in SENSOR_TYPES]


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
                            YandexSensor(
                                quasar,
                                device,
                                prop["parameters"]["name"],
                                description,
                            )
                        )

    async_add_entities(devices, True)


# noinspection PyAbstractClass
class YandexSensor(SensorEntity):
    """Yandex Home sensor entity"""

    _humidity = None
    _temperature = None
    _pressure = None
    _illumination = None
    _motion = None

    def __init__(
        self,
        quasar: YandexQuasar,
        device: dict,
        name: str,
        description: SensorEntityDescription,
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
    def humidity(self) -> int:
        """Return current humidity."""
        return self._humidity

    @property
    def temperature(self) -> int:
        """Return current temperature."""
        return self._temperature

    @property
    def pressure(self) -> int:
        """Return current pressure."""
        return self._pressure

    @property
    def illumination(self) -> int:
        """Return current illumination."""
        return self._illumination

    @property
    def motion(self) -> int:
        """Return last motion event."""
        return self._motion

    async def async_update(self):
        """Update the entity."""
        data = await self.quasar.get_device(self.device["id"])
        instances = []

        for prop in data["properties"]:
            instance = prop["parameters"]["instance"]
            instances.append(instance)
            if instance == "humidity":
                self._humidity = prop["state"]["value"]
            if instance == "temperature":
                self._temperature = prop["state"]["value"]
            if instance == "pressure":
                self._pressure = prop["state"]["value"]
            if instance == "illumination":
                self._illumination = prop["state"]["value"]
            if instance == "motion":
                self._motion = prop["state"]["value"]

        
        if "motion" not in instances:
            self._motion = "cleared"

    @property
    def native_value(self) -> Any:
        """Return the native value of the sensor."""
        return getattr(self, self.entity_description.key)
