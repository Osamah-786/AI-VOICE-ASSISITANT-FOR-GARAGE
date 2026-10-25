import asyncio
import logging
import sqlite3
from typing import Annotated

from livekit.agents import llm

from db_driver import DatabaseDriver

logger = logging.getLogger("user-data")
DB = DatabaseDriver()


def _normalize_vin(vin: str) -> str:
    return "".join(vin.upper().split())


def _validate_vin(vin: str) -> str | None:
    if len(vin) != 17 or any(char in "IOQ" for char in vin):
        return "A standard VIN has 17 characters and does not use I, O, or Q. Please check it and try again."
    if not vin.isalnum():
        return "The VIN can contain only letters and numbers. Please check it and try again."
    return None


class AssistantFnc:
    """Vehicle profile tools available to one agent session."""

    def __init__(self) -> None:
        self._car_details = None

    @staticmethod
    def _format_car(car) -> str:
        return f"VIN: {car.vin}; Make: {car.make}; Model: {car.model}; Year: {car.year}"

    @llm.function_tool(description="Look up a customer's vehicle profile using its 17-character VIN.")
    async def lookup_car(
        self,
        vin: Annotated[str, "The customer's vehicle identification number"],
    ) -> str:
        normalized_vin = _normalize_vin(vin)
        validation_error = _validate_vin(normalized_vin)
        if validation_error:
            return validation_error

        car = await asyncio.to_thread(DB.get_car_by_vin, normalized_vin)
        if car is None:
            self._car_details = None
            return "No vehicle profile was found for that VIN. Ask the customer whether they want to create a profile, then collect and confirm the make, model, and year."

        self._car_details = car
        logger.info("Vehicle profile found")
        return f"Vehicle profile found: {self._format_car(car)}. Confirm these details with the customer."

    @llm.function_tool(description="Return the vehicle details already identified in this conversation.")
    async def get_car_details(self) -> str:
        if self._car_details is None:
            return "No vehicle profile has been identified in this conversation yet. Ask for the VIN and look it up first."
        return self._format_car(self._car_details)

    @llm.function_tool(description="Create a vehicle profile after the customer confirms the VIN, make, model, and year.")
    async def create_car(
        self,
        vin: Annotated[str, "The customer's 17-character vehicle identification number"],
        make: Annotated[str, "Vehicle manufacturer, such as Toyota"],
        model: Annotated[str, "Vehicle model, such as Camry"],
        year: Annotated[int, "Model year between 1886 and 2100"],
    ) -> str:
        normalized_vin = _normalize_vin(vin)
        validation_error = _validate_vin(normalized_vin)
        if validation_error:
            return validation_error
        make = make.strip()
        model = model.strip()
        if not make or not model:
            return "Make and model are required. Ask the customer for both before creating the profile."
        if not 1886 <= year <= 2100:
            return "The model year must be between 1886 and 2100. Confirm the year with the customer."

        try:
            car = await asyncio.to_thread(DB.create_car, normalized_vin, make, model, year)
        except sqlite3.IntegrityError:
            existing = await asyncio.to_thread(DB.get_car_by_vin, normalized_vin)
            if existing is not None:
                self._car_details = existing
                return f"A profile already exists for this VIN: {self._format_car(existing)}. Confirm those details with the customer."
            logger.exception("Could not create vehicle profile")
            return "The vehicle profile could not be saved. Please try again later."
        except sqlite3.Error:
            logger.exception("Could not create vehicle profile")
            return "The vehicle profile could not be saved. Please try again later."

        self._car_details = car
        logger.info("Vehicle profile created")
        return f"Vehicle profile created: {self._format_car(car)}. Confirm the saved details with the customer."
