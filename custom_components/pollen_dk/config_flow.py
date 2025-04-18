"""Config flow for Pollen DK integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant
# from homeassistant.exceptions import HomeAssistantError # Uncomment if needed for validation

from .const import DOMAIN, REGION_IDS, POLLEN_IDS # Import constants

_LOGGER = logging.getLogger(__name__)

# Optional: Define a schema if you want user input during setup.
# For now, we'll skip user input and use defaults.
# STEP_USER_DATA_SCHEMA = vol.Schema(
#     {
#         vol.Optional(CONF_REGIONS): cv.multi_select(REGION_IDS),
#         vol.Optional(CONF_POLLEN_TYPES): cv.multi_select(POLLEN_IDS),
#     }
# )

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # Here you could potentially validate API keys or other inputs.
    # Since this integration doesn't require specific auth or connection tests
    # before setup, we can keep this simple or even remove it if no validation needed.
    # If validation fails, raise an exception like CannotConnect or InvalidAuth.
    # Example:
    # if not await test_api_connection(data["api_key"]):
    #     raise CannotConnect("Failed to connect to the API")
    pass # No validation needed for this integration's setup


class PollenDkConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pollen DK."""

    VERSION = 1
    # ConnectionClassName = config_entries.CONN_CLASS_CLOUD_POLL # Optional: Specify connection class

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        # Only allow a single instance of the integration
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            # Here you would process user_input if you had a schema
            # For now, we create an entry with empty data, relying on defaults
            # in async_setup_entry.
            # You could add validation here using validate_input if needed.
            # errors = {}
            # try:
            #     await validate_input(self.hass, user_input)
            # except CannotConnect:
            #     errors["base"] = "cannot_connect"
            # except InvalidAuth:
            #     errors["base"] = "invalid_auth"
            # except Exception:  # pylint: disable=broad-except
            #     _LOGGER.exception("Unexpected exception")
            #     errors["base"] = "unknown"
            # else:
            #     return self.async_create_entry(title="Pollen DK", data=user_input) # If using schema

            _LOGGER.debug("Creating Pollen DK config entry with default settings")
            return self.async_create_entry(title="Pollen DK", data={})

        # If user_input is None, show the form.
        # Since we don't have options yet, we just proceed to create the entry.
        # If we had STEP_USER_DATA_SCHEMA, we would show the form like this:
        # return self.async_show_form(
        #     step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        # )

        # For no-input setup, directly create the entry.
        _LOGGER.debug("Showing config flow step 'user' for Pollen DK (no input required)")
        return self.async_show_form(step_id="user") # Show a confirmation form


# Optional: Define exceptions for specific validation errors
# class CannotConnect(HomeAssistantError):
#     """Error to indicate we cannot connect."""

# class InvalidAuth(HomeAssistantError):
#     """Error to indicate there is invalid auth."""
