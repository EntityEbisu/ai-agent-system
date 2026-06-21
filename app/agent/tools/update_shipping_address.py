"""Tool: update_shipping_address — updates a customer's shipping address.

The LLM uses this when the user wants to change their delivery address.
"""

import json
import sqlite3
from pathlib import Path

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class AddressModel(BaseModel):
    """A physical mailing address."""

    street: str = Field(..., min_length=1, description="Street address (e.g. '123 Main St')")
    city: str = Field(..., min_length=1, description="City name")
    state: str = Field(
        ..., min_length=2, max_length=2, pattern=r"^[A-Z]{2}$",
        description="Two-letter state code (e.g. 'CA', 'NY')",
    )
    zip: str = Field(
        ..., pattern=r"^\d{5}(-\d{4})?$",
        description="ZIP or postal code (e.g. '97201' or '97201-1234')",
    )


class UpdateShippingAddressArgs(BaseModel):
    """Arguments for updating a customer's shipping address."""

    user_id: str = Field(
        ..., min_length=1, description="The customer's unique user ID"
    )
    address: AddressModel = Field(
        ..., description="The new shipping address (street, city, state, zip)"
    )


class UpdateShippingAddressTool(BaseTool):
    """Update a customer's saved shipping address.

    The new address replaces the existing address on file.  Returns a
    confirmation with the updated address so the customer can verify it.
    """

    name: str = "update_shipping_address"
    description: str = (
        "Update the shipping address on a customer's account. "
        "Use this when a customer asks to change their delivery address. "
        "The address must include street, city, two-letter state code, and ZIP code."
    )
    args_schema: type[BaseModel] = UpdateShippingAddressArgs
    db_path: str = "data/sqlite/conversations.db"
    """Path to the SQLite database with the ``users`` table."""

    def _run(self, user_id: str, address: dict) -> str:
        """Execute the address update synchronously."""
        conn = sqlite3.connect(str(Path(self.db_path)))
        try:
            # Check user exists first
            cursor = conn.execute(
                "SELECT user_id FROM users WHERE user_id = ?", (user_id,)
            )
            if not cursor.fetchone():
                return f"No profile found for user ID '{user_id}'. Cannot update address."

            address_json = json.dumps(address)
            conn.execute(
                "UPDATE users SET shipping_address = ? WHERE user_id = ?",
                (address_json, user_id),
            )
            conn.commit()

            addr = address
            addr_str = (
                f"{addr.get('street', '')}, "
                f"{addr.get('city', '')}, "
                f"{addr.get('state', '')} "
                f"{addr.get('zip', '')}"
            ).strip(", ")
            return (
                f"Shipping address updated successfully for user '{user_id}'.\n"
                f"New address: {addr_str}\n"
                f"Please verify this is correct."
            )
        finally:
            conn.close()

    async def _arun(self, user_id: str, address: dict) -> str:
        """Async variant delegates to sync."""
        return self._run(user_id=user_id, address=address)
