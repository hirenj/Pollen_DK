from __future__ import annotations

import logging
from typing import Any, Callable # Add Any import

from homeassistant.config_entries import ConfigEntry # Add ConfigEntry import
from homeassistant.const import ATTR_ATTRIBUTION
from homeassistant.core import HomeAssistant # Add HomeAssistant import
from homeassistant.helpers.entity_platform import AddEntitiesCallback # Add AddEntitiesCallback import
from homeassistant.helpers.update_coordinator import CoordinatorEntity # Import CoordinatorEntity

from .const import (
    CONF_CLIENT,
    # CONF_PLATFORM, # No longer needed here
    CREDITS,
    DOMAIN,
    NAME_PREFIX,
    # UPDATE_INTERVAL, # No longer needed here
)
# from datetime import timedelta # No longer needed here

from homeassistant.components.sensor import SensorEntity, SensorStateClass # Keep SensorEntity for typing if needed, SensorStateClass
# from homeassistant.helpers.update_coordinator import DataUpdateCoordinator # No longer needed here

from .pollen_dk_api import Pollen_DK, PollenRegion, PollenType # Import API classes for type hinting

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    # Retrieve the coordinator and client from hass data
    entry_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = entry_data["coordinator"]
    pollen_DK: Pollen_DK = entry_data[CONF_CLIENT] # Add type hint

    # Add the sensor to Home Assistant
    entities = []
    regions = pollen_DK.getRegions() # This should ideally use coordinator.data if update returns data
    # However, the current API client updates its internal state, so accessing it directly is okay here.
    # The getRegions() method seems to return dict_values, so we iterate directly
    # and get the ID from the region object.
    regions_list = list(regions) # Convert dict_values to list for len() and iteration
    regions_len = len(regions_list)
    for region in regions_list: # Iterate over PollenRegion objects
        region_id = region.getID() # Get ID from the object
        for pollen in [*region.getPollenTypes()]:
            entities.append(
                PollenSensor(coordinator, pollen_DK, region_id, pollen.getID(), regions_len)
            )
    async_add_entities(entities)


class PollenSensor(CoordinatorEntity, SensorEntity): # Inherit from CoordinatorEntity
    """Representation of a Pollen Sensor."""

    # Set `_attr_has_entity_name = True` if using Name property helper, else False or omit.
    # _attr_has_entity_name = True # Requires HA Core 2021.12+

    def __init__(self, coordinator, client: Pollen_DK, regionID: int, pollenID: int, regionsLen: int) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator) # Initialize CoordinatorEntity
        self._client = client # Store the API client instance
        self._regionID = regionID
        self._pollenID = pollenID
        self._regionsLen = regionsLen
        self._attr_state_class = SensorStateClass.MEASUREMENT
        # Generate unique ID based on coordinator entry_id and sensor specifics
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{self._regionID}_{self._pollenID}"
        # Device Info: Link sensor to a device representing the region or the integration instance
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"region_{self._regionID}")}, # Unique identifier for the device
            "name": self.region().getName(), # Name of the device (Region Name)
            "manufacturer": "Astma-Allergi Danmark", # Optional: Or your integration name
            "model": "Pollen Data", # Optional
            "via_device": (DOMAIN, coordinator.config_entry.entry_id), # Link to the integration entry device if desired
        }
        # Set initial name - will be updated by property
        self._attr_name = self._generate_sensor_name()


    def _generate_sensor_name(self) -> str:
        """Generate the sensor name based on region count."""
        pollen_name = self.pollen().getName()
        if self._regionsLen > 1:
            region_short_name = self.region().getName().split()[0] # Assumes "Vest" or "Øst"
            return f"{NAME_PREFIX} {pollen_name} {region_short_name}"
        else:
            return f"{NAME_PREFIX} {pollen_name}"

    # Helper methods to get current region/pollen data from the client instance
    def region(self) -> PollenRegion:
        print('region',self._client.getRegionByID(self._regionID))
        """Return the region object from the client."""
        # Access the client stored during init
        return self._client.getRegionByID(self._regionID)

    def pollen(self) -> PollenType:
        print('pollen',self.region().getPollenTypeByID(self._pollenID))
        """Return the pollen object from the client."""
        return self.region().getPollenTypeByID(self._pollenID)

    def name(self) -> str:
        print(self._generate_sensor_name())
        """Return the name of the sensor."""
        # Consider using self._attr_name which is set in __init__
        # If the name needs to be dynamic based on state, keep this property.
        # Otherwise, setting self._attr_name in __init__ is preferred.
        return self._generate_sensor_name() # Use the helper

    @property
    def icon(self) -> str:
        """Return the icon of the sensor."""
        return "mdi:flower-pollen"

    @property
    def state(self) -> int | None:
        """Return the state of the sensor."""
        # Data is fetched by the coordinator, access it via the client
        try:
            return self.pollen().getLevel()
        except (KeyError, AttributeError):
            # Handle cases where data might not be available yet or after an error
            _LOGGER.warning(f"Could not retrieve level for pollen {self._pollenID} in region {self._regionID}")
            return None

    # unique_id is now set using self._attr_unique_id in __init__

    # state_class is set using self._attr_state_class in __init__

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attr = {}
        try:
            pollen_data = self.pollen()
            attr["last_update"] = pollen_data.getDate()
            attr["in_season"] = pollen_data.getInSeason()
            attr["predictions"] = [
                {"date": pred.getDate(), "level": pred.getLevel()}
                for pred in pollen_data.getPredictions()
            ]
        except (KeyError, AttributeError):
            # Handle cases where data might not be available
             _LOGGER.warning(f"Could not retrieve attributes for pollen {self._pollenID} in region {self._regionID}")
             attr["last_update"] = None
             attr["in_season"] = None
             attr["predictions"] = []

        attr[ATTR_ATTRIBUTION] = ", ".join([f"{k}: {v}" for d in CREDITS for k, v in d.items()]) # Format credits better

        return attr

    # should_poll is implicitly False for CoordinatorEntity
    # available is handled by CoordinatorEntity
    # async_update is handled by CoordinatorEntity
    # async_added_to_hass listener setup is handled by CoordinatorEntity

    # Optional: Add this if you need to react to coordinator updates specifically
    # @callback
    # def _handle_coordinator_update(self) -> None:
    #     """Handle updated data from the coordinator."""
    #     # This is called when the coordinator has new data.
    #     # Update the name if it can change dynamically
    #     self._attr_name = self._generate_sensor_name()
    #     self.async_write_ha_state() # Update entity state
