from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .pollen_dk_api import Pollen_DK

from .const import (
    DOMAIN,
    CONF_CLIENT,
    CONF_POLLEN_TYPES,
    CONF_REGIONS,
    POLLEN_IDS,
    REGION_IDS,
    UPDATE_INTERVAL, # Added import
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pollen DK from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Get region and pollen IDs from the config entry options or data
    # Assuming options flow is not implemented yet, use data
    # Convert stored string keys back to int IDs if necessary (depends on config flow)
    # For now, assume they are stored correctly as integers or retrieved from const
    region_ids = entry.data.get(CONF_REGIONS, list(REGION_IDS.values()))
    pollen_ids = entry.data.get(CONF_POLLEN_TYPES, list(POLLEN_IDS.values()))

    _LOGGER.debug(f"Setting up entry {entry.entry_id} with regions: {region_ids}, pollen types: {pollen_ids}")

    # Create API instance
    api_client = Pollen_DK(region_ids, pollen_ids)

    # Create DataUpdateCoordinator
    async def async_update_data():
        """Fetch data from API endpoint."""
        try:
            # Note: update() is synchronous, so run it in executor
            await hass.async_add_executor_job(api_client.update)
            # Return some data if needed by entities, otherwise None is fine
            # For this integration, entities access the client directly via hass.data
            return None
        except Exception as err:
            _LOGGER.error(f"Error communicating with API: {err}")
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"{DOMAIN}_{entry.entry_id}", # Unique name per entry
        update_method=async_update_data,
        update_interval=timedelta(minutes=UPDATE_INTERVAL),
    )

    # Fetch initial data so we have data when entities subscribe
    # async_config_entry_first_refresh replaces async_request_refresh in HA core >= 2021.12
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator and API client in hass.data, keyed by entry_id
    hass.data[DOMAIN][entry.entry_id] = {
        CONF_CLIENT: api_client,
        "coordinator": coordinator,
    }

    # Forward the setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # TODO: Add update listener for options flow if implemented later
    # entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug(f"Unloading entry {entry.entry_id}")
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Remove coordinator and API client from hass.data
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]: # Remove domain entry if it's the last config entry
            hass.data.pop(DOMAIN)
        _LOGGER.debug(f"Successfully unloaded entry {entry.entry_id}")

    return unload_ok

# Optional: If you implement options flow later, add this listener
# async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
#     """Handle options update."""
#     _LOGGER.debug("Configuration options updated, reloading integration")
#     await hass.config_entries.async_reload(entry.entry_id)
