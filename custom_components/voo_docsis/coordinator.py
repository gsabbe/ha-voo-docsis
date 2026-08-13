"""DataUpdateCoordinator for Technicolor VOO DOCSIS integration."""
from datetime import timedelta
import logging
from typing import Any, Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CannotConnect, InvalidAuth, VooTechnicolorApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class VooDocsisDataUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Class to manage fetching DOCSIS metrics from VOO router."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: VooTechnicolorApi,
        scan_interval: int,
    ) -> None:
        """Initialize the coordinator."""
        self.api = api
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from VOO Technicolor Modem API."""
        try:
            raw_data = await self.api.async_get_all_data()
            return self._parse_data(raw_data)
        except (CannotConnect, InvalidAuth) as err:
            raise UpdateFailed(f"Error communicating with VOO modem: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching VOO DOCSIS metrics")
            raise UpdateFailed(f"Unexpected error: {err}") from err

    def _parse_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw modem API tables into clean sensor metrics."""
        modem_data = raw_data.get("modem", {})
        system_data = raw_data.get("system", {})

        # System Metrics
        cpu_usage = system_data.get("CPUUsage")
        mem_free = system_data.get("MemFree")
        mem_total = system_data.get("MemTotal")
        uptime = system_data.get("UpTime")
        software_version = system_data.get("SoftwareVersion")
        model_name = system_data.get("ModelName") or system_data.get("Manufacturer") or "Technicolor Modem"
        cm_status = modem_data.get("CMStatus") or system_data.get("CMStatus") or "UNKNOWN"

        # Channels parsing
        us_tbl = modem_data.get("USTbl", [])
        ds_tbl = modem_data.get("DSTbl", [])
        ex_ds_tbl = modem_data.get("exDSTbl", [])
        err_tbl = modem_data.get("ErrTbl", [])

        # Filter locked upstream channels
        active_us = [ch for ch in us_tbl if isinstance(ch, dict) and ch.get("LockStatus") == "Locked"]
        
        # Filter locked downstream channels (both SC-QAM and OFDM)
        active_ds_scqam = [ch for ch in ds_tbl if isinstance(ch, dict) and (ch.get("LockStatus") == "Locked" or (ch.get("Frequency") and ch.get("Frequency") != "" and ch.get("Frequency") != "0"))]
        active_ds_ofdm = [ch for ch in ex_ds_tbl if isinstance(ch, dict) and (ch.get("LockStatus") == "Locked" or (ch.get("CentralFrequency") and ch.get("CentralFrequency") != ""))]
        total_active_ds = len(active_ds_scqam) + len(active_ds_ofdm)

        # Calculate total error codewords
        total_correcteds = 0
        total_uncorrectables = 0
        for err in err_tbl:
            if isinstance(err, dict):
                try:
                    total_correcteds += int(err.get("Correcteds", 0))
                    total_uncorrectables += int(err.get("Uncorrectables", 0))
                except (ValueError, TypeError):
                    pass

        # OFDM metrics
        ofdm_power = None
        ofdm_snr = None
        if ex_ds_tbl and isinstance(ex_ds_tbl, list) and len(ex_ds_tbl) > 0:
            first_ofdm = ex_ds_tbl[0]
            if isinstance(first_ofdm, dict):
                pwr_str = first_ofdm.get("PowerLevel", "")
                snr_str = first_ofdm.get("SNRLevel", "")
                try:
                    ofdm_power = float(pwr_str.replace("dBmV", "").strip())
                except (ValueError, AttributeError):
                    pass
                try:
                    ofdm_snr = float(snr_str.replace("dB", "").strip())
                except (ValueError, AttributeError):
                    pass

        return {
            "cm_status": cm_status,
            "cpu_usage": float(cpu_usage) if cpu_usage is not None and str(cpu_usage).replace('.', '', 1).isdigit() else None,
            "mem_free_mb": round(int(mem_free) / 1024.0, 1) if mem_free is not None and str(mem_free).isdigit() else None,
            "mem_total_mb": round(int(mem_total) / 1024.0, 1) if mem_total is not None and str(mem_total).isdigit() else None,
            "uptime": int(uptime) if uptime is not None and str(uptime).isdigit() else None,
            "software_version": software_version,
            "model_name": model_name,
            "active_upstream_channels": len(active_us),
            "active_downstream_channels": total_active_ds,
            "total_correcteds": total_correcteds,
            "total_uncorrectables": total_uncorrectables,
            "ofdm_power_level": ofdm_power,
            "ofdm_snr_level": ofdm_snr,
            "upstream_channels": us_tbl,
            "downstream_channels": ds_tbl,
            "ofdm_channels": ex_ds_tbl,
            "raw_system": system_data,
        }
