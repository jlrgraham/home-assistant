"""Support for Tractive sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_BATTERY_LEVEL,
    PERCENTAGE,
    EntityCategory,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from . import Trackables, TractiveClient
from .const import (
    ATTR_ACTIVITY_LABEL,
    ATTR_CALORIES,
    ATTR_DAILY_GOAL,
    ATTR_MINUTES_ACTIVE,
    ATTR_MINUTES_DAY_SLEEP,
    ATTR_MINUTES_NIGHT_SLEEP,
    ATTR_MINUTES_REST,
    ATTR_SLEEP_LABEL,
    ATTR_TRACKER_STATE,
    CLIENT,
    DOMAIN,
    TRACKABLES,
    TRACKER_ACTIVITY_STATUS_UPDATED,
    TRACKER_HARDWARE_STATUS_UPDATED,
    TRACKER_WELLNESS_STATUS_UPDATED,
)
from .entity import TractiveEntity


@dataclass
class TractiveRequiredKeysMixin:
    """Mixin for required keys."""

    signal_prefix: str


@dataclass
class TractiveSensorEntityDescription(
    SensorEntityDescription, TractiveRequiredKeysMixin
):
    """Class describing Tractive sensor entities."""

    hardware_sensor: bool = False
    value_fn: Callable[[StateType], StateType] = lambda state: state


class TractiveSensor(TractiveEntity, SensorEntity):
    """Tractive sensor."""

    entity_description: TractiveSensorEntityDescription

    def __init__(
        self,
        client: TractiveClient,
        item: Trackables,
        description: TractiveSensorEntityDescription,
    ) -> None:
        """Initialize sensor entity."""
        if description.hardware_sensor:
            dispatcher_signal = (
                f"{description.signal_prefix}-{item.tracker_details['_id']}"
            )
        else:
            dispatcher_signal = f"{description.signal_prefix}-{item.trackable['_id']}"
        super().__init__(
            client, item.trackable, item.tracker_details, dispatcher_signal
        )

        self._attr_unique_id = f"{item.trackable['_id']}_{description.key}"
        self._attr_available = False
        self.entity_description = description

    @callback
    def handle_status_update(self, event: dict[str, Any]) -> None:
        """Handle status update."""
        self._attr_native_value = self.entity_description.value_fn(
            event[self.entity_description.key]
        )

        super().handle_status_update(event)


SENSOR_TYPES: tuple[TractiveSensorEntityDescription, ...] = (
    TractiveSensorEntityDescription(
        key=ATTR_BATTERY_LEVEL,
        translation_key="tracker_battery_level",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        signal_prefix=TRACKER_HARDWARE_STATUS_UPDATED,
        hardware_sensor=True,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    TractiveSensorEntityDescription(
        key=ATTR_TRACKER_STATE,
        translation_key="tracker_state",
        signal_prefix=TRACKER_HARDWARE_STATUS_UPDATED,
        hardware_sensor=True,
        icon="mdi:radar",
        entity_category=EntityCategory.DIAGNOSTIC,
        device_class=SensorDeviceClass.ENUM,
        options=[
            "not_reporting",
            "operational",
            "system_shutdown_user",
            "system_startup",
        ],
    ),
    TractiveSensorEntityDescription(
        key=ATTR_MINUTES_ACTIVE,
        translation_key="activity_time",
        icon="mdi:clock-time-eight-outline",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        signal_prefix=TRACKER_ACTIVITY_STATUS_UPDATED,
        state_class=SensorStateClass.TOTAL,
    ),
    TractiveSensorEntityDescription(
        key=ATTR_MINUTES_REST,
        translation_key="rest_time",
        icon="mdi:clock-time-eight-outline",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        signal_prefix=TRACKER_WELLNESS_STATUS_UPDATED,
        state_class=SensorStateClass.TOTAL,
    ),
    TractiveSensorEntityDescription(
        key=ATTR_CALORIES,
        translation_key="calories",
        icon="mdi:fire",
        native_unit_of_measurement="kcal",
        signal_prefix=TRACKER_WELLNESS_STATUS_UPDATED,
        state_class=SensorStateClass.TOTAL,
    ),
    TractiveSensorEntityDescription(
        key=ATTR_DAILY_GOAL,
        translation_key="daily_goal",
        icon="mdi:flag-checkered",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        signal_prefix=TRACKER_ACTIVITY_STATUS_UPDATED,
    ),
    TractiveSensorEntityDescription(
        key=ATTR_MINUTES_DAY_SLEEP,
        translation_key="minutes_day_sleep",
        icon="mdi:sleep",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        signal_prefix=TRACKER_WELLNESS_STATUS_UPDATED,
        state_class=SensorStateClass.TOTAL,
    ),
    TractiveSensorEntityDescription(
        key=ATTR_MINUTES_NIGHT_SLEEP,
        translation_key="minutes_night_sleep",
        icon="mdi:sleep",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        signal_prefix=TRACKER_WELLNESS_STATUS_UPDATED,
        state_class=SensorStateClass.TOTAL,
    ),
    TractiveSensorEntityDescription(
        key=ATTR_SLEEP_LABEL,
        translation_key="sleep",
        icon="mdi:sleep",
        signal_prefix=TRACKER_WELLNESS_STATUS_UPDATED,
        value_fn=lambda state: state.lower() if isinstance(state, str) else state,
        device_class=SensorDeviceClass.ENUM,
        options=[
            "ok",
            "good",
        ],
    ),
    TractiveSensorEntityDescription(
        key=ATTR_ACTIVITY_LABEL,
        translation_key="activity",
        icon="mdi:run",
        signal_prefix=TRACKER_WELLNESS_STATUS_UPDATED,
        value_fn=lambda state: state.lower() if isinstance(state, str) else state,
        device_class=SensorDeviceClass.ENUM,
        options=[
            "ok",
            "good",
        ],
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Tractive device trackers."""
    client = hass.data[DOMAIN][entry.entry_id][CLIENT]
    trackables = hass.data[DOMAIN][entry.entry_id][TRACKABLES]

    entities = [
        TractiveSensor(client, item, description)
        for description in SENSOR_TYPES
        for item in trackables
    ]

    async_add_entities(entities)
