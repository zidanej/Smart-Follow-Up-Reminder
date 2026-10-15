from datetime import datetime
from typing import Any, Dict, List

import streamlit as st


def format_datetime(value: str) -> str:
    if not value:
        return "Unscheduled"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone().strftime("%b %-d, %Y at %-I:%M %p")
    except ValueError:
        return value


def contact_rows(contacts: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    return [
        {
            "Name": contact["name"],
            "Company": contact.get("company") or "-",
            "Purpose": contact["purpose"],
            "Follow-up": format_datetime(contact.get("next_follow_up_at")),
            "Status": contact["status"],
        }
        for contact in contacts
    ]


def show_contacts(contacts: List[Dict[str, Any]]) -> None:
    if contacts:
        st.dataframe(
            contact_rows(contacts),
            column_config={
                "Name": st.column_config.TextColumn("Name", width="medium"),
                "Company": st.column_config.TextColumn("Company", width="medium"),
                "Purpose": st.column_config.TextColumn("Purpose", width="large"),
                "Follow-up": st.column_config.TextColumn("Follow-up", width="medium"),
                "Status": st.column_config.TextColumn("Status", width="medium"),
            },
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No contacts match this view.")
