"""Tool: check_order_status — looks up order details in the demo orders table.

The LLM uses this when the user asks about their order: "Where is my package?",
"What's the status of my order?", "When will my order arrive?".
"""
import json
import sqlite3
from datetime import date
from pathlib import Path

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field


class CheckOrderStatusArgs(BaseModel):
    """Arguments for checking an order's status."""

    name: str = Field(
        ..., min_length=1, description="Full name on the order (e.g. 'John Smith')"
    )
    ssn_last4: str = Field(
        ...,
        min_length=4,
        max_length=4,
        pattern=r"^\d{4}$",
        description="Last 4 digits of the customer's SSN",
    )
    dob: date = Field(
        ..., description="Date of birth of the customer (YYYY-MM-DD)"
    )


class CheckOrderStatusTool(BaseTool):
    """Look up one or more orders matching the customer's identity.

    Returns order status, estimated delivery date, and item list for every
    order that matches the given name + SSN last-4 + date of birth.
    """

    name: str = "check_order_status"
    description: str = (
        "Look up the status of a customer's order by name, last 4 digits of SSN, "
        "and date of birth. Returns order numbers, current status "
        "(shipped/processing/delayed/delivered), estimated delivery dates, "
        "and item descriptions for all matching orders."
    )
    args_schema: type[BaseModel] = CheckOrderStatusArgs
    db_path: str = "data/sqlite/conversations.db"
    """Path to the SQLite database with the ``orders`` table."""

    def _run(self, name: str, ssn_last4: str, dob: date) -> str:
        """Execute the order status lookup synchronously."""
        conn = sqlite3.connect(str(Path(self.db_path)))
        conn.row_factory = sqlite3.Row
        try:
            dob_str = dob.isoformat() if isinstance(dob, date) else str(dob)
            cursor = conn.execute(
                "SELECT order_id, status, estimated_delivery, items "
                "FROM orders WHERE customer_name = ? AND ssn_last4 = ? AND dob = ? "
                "ORDER BY created_at DESC",
                (name, ssn_last4, dob_str),
            )
            rows = cursor.fetchall()
            if not rows:
                return (
                    f"No orders found for '{name}' with the provided details. "
                    "Please verify the information and try again."
                )

            parts: list[str] = []
            for r in rows:
                items_list = json.loads(r["items"]) if r["items"] else []
                items_str = ", ".join(items_list) if items_list else "Unknown items"
                delivery = r["estimated_delivery"] or "TBD"
                parts.append(
                    f"Order {r['order_id']}: {r['status'].title()} — "
                    f"estimated delivery {delivery}. Items: {items_str}."
                )

            return "\n".join(parts)
        finally:
            conn.close()

    async def _arun(self, name: str, ssn_last4: str, dob: date) -> str:
        """Async variant delegates to sync."""
        return self._run(name=name, ssn_last4=ssn_last4, dob=dob)
