"""Support for Hyyp sensors."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import HyypDataUpdateCoordinator
from .entity import HyypSiteEntity, HyypPartitionEntity

PARALLEL_UPDATES = 1

SENSOR_TYPES: dict[str, SensorEntityDescription] = {
    "lastNoticeTime": SensorEntityDescription(key="lastNoticeTime"),
    "lastNoticeName": SensorEntityDescription(key="lastNoticeName"),
    "imei": SensorEntityDescription(key="imei"),
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up IDS Hyyp sensors based on a config entry."""
    coordinator: HyypDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]

    async_add_entities(
        [
            HyypSensor(coordinator, site_id, sensor)
            for site_id in coordinator.data
            for sensor, value in coordinator.data[site_id].items()
            if sensor in SENSOR_TYPES
            if value is not None
        ]
    )
    
    async_add_entities(
        [
            HyypArmedStateSensor(coordinator, site_id, partition_id)
            for site_id in coordinator.data
            for partition_id in coordinator.data[site_id]["partitions"]
        ]
    )


class HyypSensor(HyypSiteEntity, SensorEntity):
    """Representation of a IDS Hyyp sensor."""

    coordinator: HyypDataUpdateCoordinator

    def __init__(
        self,
        coordinator: HyypDataUpdateCoordinator,
        site_id: int,
        sensor: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, site_id)
        self._sensor_name = sensor
        self._attr_name = f"{self.data['name']} {sensor.title()}"
        self._attr_unique_id = f"{self._site_id}_{sensor}"
        self.entity_description = SENSOR_TYPES[sensor]

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        return self.data[self._sensor_name]



class HyypArmedStateSensor(HyypPartitionEntity, SensorEntity):
    """Representation of a IDS Hyyp sensor."""

    coordinator: HyypDataUpdateCoordinator

    def __init__(
        self,
        coordinator: HyypDataUpdateCoordinator,
        site_id: int,
        partition_id: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, site_id, partition_id)
        self._attr_name = f"{self.data['name']} {self.partition_data['name']} armed status:"
        self._attr_unique_id = f"{self._site_id}_{partition_id}_armed_status"

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.partition_data["alarm"]:
            return "Triggered"

        if self.partition_data["armed"]:
            if "stayArmed" in self.partition_data and self.partition_data["stayArmed"]:
                if 'stayArmedProfileName' in self.partition_data:
                    stayarmed_name = f"Armed {self.partition_data['stayArmedProfileName']}"
                    return stayarmed_name
                else:
                    return "Stay Armed"

            return "Away Armed"

        return "Disarmed"

