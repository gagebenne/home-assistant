"""Support for Dexcom sensors."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import UnitOfBloodGlucoseConcentration
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DexcomConfigEntry, DexcomCoordinator

TRENDS = {
    1: "rising_quickly",
    2: "rising",
    3: "rising_slightly",
    4: "steady",
    5: "falling_slightly",
    6: "falling",
    7: "falling_quickly",
    8: "unable_to_determine_trend",
    9: "trend_unavailable",
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: DexcomConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Dexcom sensors."""
    coordinator = config_entry.runtime_data
    async_add_entities(
        [
            DexcomGlucoseTrendSensor(coordinator, config_entry.entry_id),
            DexcomGlucoseValueSensor(coordinator, config_entry.entry_id),
        ],
    )


class DexcomSensorEntity(CoordinatorEntity[DexcomCoordinator], SensorEntity):
    """Base Dexcom sensor entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DexcomCoordinator,
        entry_id: str,
        key: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.dexcom.account_id}-{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            entry_type=DeviceEntryType.SERVICE,
            name=coordinator.dexcom.username,
            manufacturer="Dexcom",
        )

    @property
    def extra_state_attributes(self) -> dict[str, datetime]:
        """Return device specific state attributes."""
        if self.coordinator.data:
            return {
                # The actual glucose reading time, not when we polled for it
                "last_updated": self.coordinator.data.datetime
            }
        return {}


class DexcomGlucoseValueSensor(DexcomSensorEntity):
    """Representation of a Dexcom glucose value sensor."""

    _attr_translation_key = "glucose_value"
    _attr_device_class = SensorDeviceClass.BLOOD_GLUCOSE_CONCENTRATION
    _attr_native_unit_of_measurement = (
        UnitOfBloodGlucoseConcentration.MILLIGRAMS_PER_DECILITER
    )

    def __init__(
        self,
        coordinator: DexcomCoordinator,
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry_id, "value")

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.mg_dl
        return None


class DexcomGlucoseTrendSensor(DexcomSensorEntity):
    """Representation of a Dexcom glucose trend sensor."""

    _attr_translation_key = "glucose_trend"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = list(TRENDS.values())

    def __init__(self, coordinator: DexcomCoordinator, entry_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry_id, "trend")

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if self.coordinator.data:
            return TRENDS.get(self.coordinator.data.trend)
        return None
