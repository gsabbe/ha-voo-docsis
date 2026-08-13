"""Sensor platform for VOO Technicolor DOCSIS integration."""
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import VooDocsisDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up VOO DOCSIS sensor entities based on a config entry."""
    coordinator: VooDocsisDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=coordinator.data.get("model_name", "VOO Technicolor Cable Modem"),
        manufacturer="Technicolor",
        model=coordinator.data.get("model_name", "CGA4233VOO"),
        sw_version=coordinator.data.get("software_version"),
    )

    entities = [
        VooDocsisSensor(
            coordinator,
            device_info,
            key="cm_status",
            name="Cable Modem Status",
            icon="mdi:router-wireless",
        ),
        VooDocsisSensor(
            coordinator,
            device_info,
            key="cpu_usage",
            name="CPU Usage",
            native_unit_of_measurement="%",
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:cpu-64-bit",
        ),
        VooDocsisSensor(
            coordinator,
            device_info,
            key="mem_free_mb",
            name="Memory Free",
            native_unit_of_measurement="MB",
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:memory",
        ),
        VooDocsisSensor(
            coordinator,
            device_info,
            key="uptime",
            name="System Uptime",
            native_unit_of_measurement="s",
            state_class=SensorStateClass.TOTAL_INCREASING,
            icon="mdi:timer-outline",
        ),
        VooDocsisSensor(
            coordinator,
            device_info,
            key="active_upstream_channels",
            name="Active Upstream Channels",
            native_unit_of_measurement="channels",
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:upload-network",
        ),
        VooDocsisSensor(
            coordinator,
            device_info,
            key="active_downstream_channels",
            name="Active Downstream Channels",
            native_unit_of_measurement="channels",
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:download-network",
        ),
        VooDocsisSensor(
            coordinator,
            device_info,
            key="total_correcteds",
            name="Total Corrected Errors",
            native_unit_of_measurement="errors",
            state_class=SensorStateClass.TOTAL_INCREASING,
            icon="mdi:check-network",
        ),
        VooDocsisSensor(
            coordinator,
            device_info,
            key="total_uncorrectables",
            name="Total Uncorrectable Errors",
            native_unit_of_measurement="errors",
            state_class=SensorStateClass.TOTAL_INCREASING,
            icon="mdi:alert-network",
        ),
        VooDocsisSensor(
            coordinator,
            device_info,
            key="ofdm_power_level",
            name="OFDM Downstream Power",
            native_unit_of_measurement="dBmV",
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:wave",
        ),
        VooDocsisSensor(
            coordinator,
            device_info,
            key="ofdm_snr_level",
            name="OFDM Downstream SNR",
            native_unit_of_measurement="dB",
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:signal-variant",
        ),
    ]

    # Add dynamic per-channel power & SNR sensors for Upstream channels
    us_channels = coordinator.data.get("upstream_channels", [])
    for idx, ch in enumerate(us_channels):
        if isinstance(ch, dict) and ch.get("ChannelID"):
            ch_id = ch.get("ChannelID")
            entities.append(
                VooChannelSensor(
                    coordinator,
                    device_info,
                    channel_type="us",
                    channel_id=ch_id,
                    metric_type="power",
                    name=f"Upstream Channel {ch_id} Power",
                    native_unit_of_measurement="dBmV",
                    icon="mdi:upload-network-outline",
                )
            )

    # Add dynamic per-channel sensors for Downstream channels (SNR & Power)
    ds_channels = coordinator.data.get("downstream_channels", [])
    for idx, ch in enumerate(ds_channels):
        if isinstance(ch, dict) and ch.get("ChannelID") and ch.get("ChannelID") != "0":
            ch_id = ch.get("ChannelID")
            entities.append(
                VooChannelSensor(
                    coordinator,
                    device_info,
                    channel_type="ds",
                    channel_id=ch_id,
                    metric_type="power",
                    name=f"Downstream Channel {ch_id} Power",
                    native_unit_of_measurement="dBmV",
                    icon="mdi:download-network-outline",
                )
            )
            entities.append(
                VooChannelSensor(
                    coordinator,
                    device_info,
                    channel_type="ds",
                    channel_id=ch_id,
                    metric_type="snr",
                    name=f"Downstream Channel {ch_id} SNR",
                    native_unit_of_measurement="dB",
                    icon="mdi:signal",
                )
            )

    async_add_entities(entities, update_before_add=True)


class VooDocsisSensor(CoordinatorEntity[VooDocsisDataUpdateCoordinator], SensorEntity):
    """Base sensor for general VOO modem metrics."""

    def __init__(
        self,
        coordinator: VooDocsisDataUpdateCoordinator,
        device_info: DeviceInfo,
        key: str,
        name: str,
        native_unit_of_measurement: Optional[str] = None,
        state_class: Optional[SensorStateClass] = None,
        icon: Optional[str] = None,
    ) -> None:
        """Initialize the sensor entity."""
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"VOO Modem {name}"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{key}"
        self._attr_device_info = device_info
        self._attr_native_unit_of_measurement = native_unit_of_measurement
        self._attr_state_class = state_class
        self._attr_icon = icon

    @property
    def native_value(self) -> Any:
        """Return state from coordinator data."""
        return self.coordinator.data.get(self._key)


class VooChannelSensor(CoordinatorEntity[VooDocsisDataUpdateCoordinator], SensorEntity):
    """Sensor for individual DOCSIS Upstream/Downstream channel metrics."""

    def __init__(
        self,
        coordinator: VooDocsisDataUpdateCoordinator,
        device_info: DeviceInfo,
        channel_type: str,  # 'us' or 'ds'
        channel_id: str,
        metric_type: str,   # 'power' or 'snr'
        name: str,
        native_unit_of_measurement: Optional[str] = None,
        icon: Optional[str] = None,
    ) -> None:
        """Initialize channel metric sensor."""
        super().__init__(coordinator)
        self._channel_type = channel_type
        self._channel_id = channel_id
        self._metric_type = metric_type
        self._attr_name = f"VOO Modem {name}"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{channel_type}_{channel_id}_{metric_type}"
        self._attr_device_info = device_info
        self._attr_native_unit_of_measurement = native_unit_of_measurement
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_icon = icon

    @property
    def native_value(self) -> Any:
        """Parse metric from channel list in coordinator data."""
        channels = (
            self.coordinator.data.get("upstream_channels", [])
            if self._channel_type == "us"
            else self.coordinator.data.get("downstream_channels", [])
        )
        for ch in channels:
            if isinstance(ch, dict) and str(ch.get("ChannelID")) == str(self._channel_id):
                field = "PowerLevel" if self._metric_type == "power" else "SNRLevel"
                raw_val = ch.get(field, "")
                if not raw_val:
                    return None
                try:
                    # Clean strings like "44.5 dBmV" or "38.2 dB"
                    clean_val = raw_val.replace("dBmV", "").replace("dB", "").strip()
                    return float(clean_val)
                except (ValueError, AttributeError):
                    return raw_val
        return None
