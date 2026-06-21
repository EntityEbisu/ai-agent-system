"""Tool: get_user_profile — retrieves a customer's profile information.

The LLM uses this when the user asks about their account details,
shipping address, or contact information.
"""

import json
import sqlite3
from pathlib import Path

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class GetUserProfileArgs(BaseModel):
    """Arguments for fetching a user's profile."""

    user_id: str = Field(
        ..., min_length=1, description="The customer's unique user ID"
    )


class GetUserProfileTool(BaseTool):
    """Look up a customer's profile: name, email, and shipping address.

    Use this when you need the user's registered name, email address,
    or current shipping address on file.
    """

    name: str = "get_user_profile"
    description: str = (
        "Retrieve a customer's profile information including their full name, "
        "email address, and saved shipping address. Use this when the customer "
        "asks about their account or when you need their current address."
    )
    args_schema: type[BaseModel] = GetUserProfileArgs
    db_path: str = "data/sqlite/conversations.db"
    """Path to the SQLite database with the ``users`` table."""

    def _run(self, user_id: str) -> str:
        """Execute the profile lookup synchronously."""
        conn = sqlite3.connect(str(Path(self.db_path)))
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(
                "SELECT name, email, shipping_address FROM users WHERE user_id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return f"No profile found for user ID '{user_id}'."

            address = row["shipping_address"]
            try:
                addr_dict = json.loads(address) if address else {}
                addr_str = (
                    f"{addr_dict.get('street', '')}, "
                    f"{addr_dict.get('city', '')}, "
                    f"{addr_dict.get('state', '')} "
                    f"{addr_dict.get('zip', '')}"
                ).strip(", ")
            except (json.JSONDecodeError, TypeError):
                addr_str = str(address) if address else "No address on file"

            return (
                f"**{row['name']}**\n"
                f"Email: {row['email']}\n"
                f"Shipping Address: {addr_str}"
            )
        finally:
            conn.close()

    async def _arun(self, user_id: str) -> str:
        """Async variant delegates to sync."""
        return self._run(user_id=user_id)
