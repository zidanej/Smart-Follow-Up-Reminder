from datetime import datetime, time
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import streamlit as st

try:
    from frontend.api_client import ApiError, create_contact, create_interaction, dashboard_summary, delete_contact, follow_ups, get_contact, list_contacts, update_contact
    from frontend.components import format_datetime, show_contacts
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from api_client import ApiError, create_contact, create_interaction, dashboard_summary, delete_contact, follow_ups, get_contact, list_contacts, update_contact
    from components import format_datetime, show_contacts

st.set_page_config(page_title="Smart Follow-Up Reminder", page_icon="R", layout="wide")
st.markdown("""
<style>
:root { --green: #203A32; --green-light: #2F5146; --paper: #F7F5EF; --card: #FFFFFF; --ink: #1B2923; --secondary: #5F6B64; --line: #D5DDD7; --header: #18211E; --header-button: #34443D; --info-bg: #DCEAF4; --info-ink: #203747; --danger: #7A2E2E; }
html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .stApp { background: var(--paper) !important; color: var(--ink) !important; }
.stApp, .stApp * { font-family: "Avenir Next", "Helvetica Neue", Arial, sans-serif; }
[data-testid="stMainBlockContainer"] { max-width: 1440px; padding: 40px 48px 64px; }
.stApp p, .stApp li, .stApp label, .stApp [data-testid="stMarkdownContainer"] { color: var(--ink); }
.stApp small, .stCaption, [data-testid="stCaptionContainer"] { color: var(--secondary) !important; }
h1, h2, h3, h4 { color: var(--ink) !important; letter-spacing: 0; }
h1 { font-size: 30px !important; line-height: 1.2 !important; margin: 0 0 8px !important; }
h2 { font-size: 22px !important; line-height: 1.3 !important; margin: 32px 0 16px !important; }
h3 { font-size: 18px !important; line-height: 1.35 !important; margin: 28px 0 12px !important; }
[data-testid="stHeader"] { background: var(--header) !important; border-bottom: 1px solid var(--green-light); color: #FFFFFF !important; }
[data-testid="stDecoration"] { background: var(--green-light) !important; height: 3px !important; }
[data-testid="stHeader"] [data-testid="stToolbar"], [data-testid="stHeader"] [data-testid="stAppDeployButton"] { color: #FFFFFF !important; }
[data-testid="stHeader"] button { min-height: 36px; color: #FFFFFF !important; background: var(--header-button) !important; border: 1px solid var(--green-light) !important; border-radius: 6px; }
[data-testid="stHeader"] button:hover, [data-testid="stHeader"] button:focus-visible { background: var(--green-light) !important; color: #FFFFFF !important; }
[data-testid="stHeader"] button *, [data-testid="stMainMenu"] button, [data-testid="stMainMenu"] button * { color: #FFFFFF !important; fill: #FFFFFF !important; stroke: #FFFFFF !important; }
[data-testid="stHeader"] svg path[fill="none"], [data-testid="stSidebarCollapseButton"] svg path[fill="none"] { fill: none !important; stroke: none !important; }
[data-testid="stSidebarCollapseButton"] button, [data-testid="stSidebarCollapseButton"] button * { color: #FFFFFF !important; fill: #FFFFFF !important; stroke: #FFFFFF !important; }
[data-testid="stSidebar"] { background: var(--green) !important; border-right: 1px solid var(--green-light); }
[data-testid="stSidebar"] * { color: #FFFFFF !important; }
[data-testid="stSidebar"] [role="radiogroup"] { gap: 4px; }
[data-testid="stSidebar"] input[type="radio"] { accent-color: var(--green-light) !important; }
[data-testid="stSidebar"] [role="radiogroup"] label { min-height: 40px; padding: 8px 12px; border: 1px solid transparent; border-radius: 6px; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: var(--green-light); border-color: var(--line); }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background: var(--green-light); border-color: #FFFFFF; }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) * { color: #FFFFFF !important; }
[data-testid="stMetric"] { min-height: 118px; box-sizing: border-box; background: var(--card) !important; border: 1px solid var(--line); padding: 20px !important; border-radius: 6px; }
[data-testid="stMetricLabel"] { color: var(--secondary) !important; font-size: 14px !important; line-height: 1.3 !important; }
[data-testid="stMetricValue"] { color: var(--ink) !important; font-size: 32px !important; line-height: 1.15 !important; }
.stApp input, .stApp textarea, [data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div { background: var(--card) !important; border: 1px solid #B8B8B8 !important; border-radius: 4px; }
.stApp input, .stApp textarea, [data-baseweb="input"] input, [data-baseweb="textarea"] textarea, [data-baseweb="select"] * { color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important; caret-color: var(--ink); }
.stApp input, .stApp textarea { box-shadow: none !important; text-decoration: none !important; }
.stApp input:focus, .stApp textarea:focus, [data-baseweb="select"] > div:focus-within { border-color: var(--green-light) !important; outline: 2px solid var(--green-light) !important; outline-offset: 1px; }
.stApp [data-testid="stDateInput"] input, .stApp [data-testid="stTimeInput"] input, .stApp input[type="date"], .stApp input[type="time"] { background: var(--card) !important; color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important; color-scheme: light; }
.stApp input::placeholder, .stApp textarea::placeholder { color: var(--secondary) !important; opacity: 1; }
[data-baseweb="popover"], [data-baseweb="menu"], [data-baseweb="popover"] *, [data-baseweb="menu"] * { background: var(--card) !important; color: var(--ink) !important; }
[data-testid="stElementToolbar"] button, [data-testid="stElementToolbar"] button * { color: var(--ink) !important; fill: var(--ink) !important; stroke: var(--ink) !important; }
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 6px; overflow: hidden; }
[data-testid="stAlert"] { background: var(--info-bg) !important; color: var(--info-ink) !important; border: 1px solid #AFC7D6; border-radius: 6px; }
[data-testid="stAlert"] * { color: var(--info-ink) !important; }
[data-testid="stFormSubmitButton"] button { min-height: 42px; color: #FFFFFF !important; background: var(--green) !important; border: 1px solid var(--green) !important; border-radius: 4px; padding: 8px 18px; }
[data-testid="stFormSubmitButton"] button:hover, [data-testid="stFormSubmitButton"] button:focus-visible { background: var(--green-light) !important; color: #FFFFFF !important; }
[data-testid="stButton"] button { min-height: 42px; color: var(--ink) !important; background: var(--card) !important; border: 1px solid var(--green) !important; border-radius: 4px; padding: 8px 18px; }
[data-testid="stButton"] button:hover, [data-testid="stButton"] button:focus-visible { background: var(--green) !important; color: #FFFFFF !important; }
[data-testid="stButton"] button[kind="secondary"] { color: var(--danger) !important; border-color: var(--danger) !important; }
[data-testid="stButton"] button[kind="secondary"]:hover, [data-testid="stButton"] button[kind="secondary"]:focus-visible { background: var(--danger) !important; color: #FFFFFF !important; }
[data-testid="stButton"] button[kind="secondary"] { color: var(--danger) !important; border-color: var(--danger) !important; }
[data-testid="stButton"] button[kind="secondary"]:hover, [data-testid="stButton"] button[kind="secondary"]:focus-visible { background: var(--danger) !important; color: #FFFFFF !important; }
input::-webkit-contacts-auto-fill-button, input::-webkit-credentials-auto-fill-button, input::-webkit-search-cancel-button { display: none !important; visibility: hidden !important; pointer-events: none; }
.badge { display: inline-block; padding: 4px 8px; border: 1px solid var(--line); border-radius: 4px; font-size: 13px; background: #F0F0F0; color: var(--ink); }
@media (max-width: 900px) { [data-testid="stMainBlockContainer"] { padding: 28px 24px 48px; } }
@media (max-width: 600px) { [data-testid="stMainBlockContainer"] { padding: 24px 16px 40px; } h1 { font-size: 26px !important; } [data-testid="stMetric"] { min-height: 96px; padding: 16px !important; } [data-testid="stMetricValue"] { font-size: 26px !important; } }
</style>
""", unsafe_allow_html=True)


def api_call(function: Any, *args: Any, **kwargs: Any) -> Optional[Any]:
    try:
        return function(*args, **kwargs)
    except ApiError as exc:
        st.error(str(exc))
        return None


def to_iso(date_value: Any, time_value: Any) -> Optional[str]:
    if date_value is None:
        return None
    return datetime.combine(date_value, time_value or time(9, 0)).astimezone().isoformat()


def contact_form(prefix: str, contact: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    existing = contact or {}
    existing_follow_up = existing.get("next_follow_up_at")
    existing_last = existing.get("last_contacted_at")
    form_key = prefix
    if prefix == "new-contact":
        form_key = "%s-%s" % (prefix, st.session_state.get("new_contact_form_version", 0))
    with st.form(form_key):
        name = st.text_input("Name *", value=existing.get("name", ""))
        company = st.text_input("Company", value=existing.get("company") or "")
        email = st.text_input("Email", value=existing.get("email") or "")
        phone = st.text_input("Phone", value=existing.get("phone") or "")
        purpose = st.text_input("Purpose *", value=existing.get("purpose", ""))
        status = st.selectbox("Status", ["Pending", "Replied", "Completed", "No Response"], index=["Pending", "Replied", "Completed", "No Response"].index(existing.get("status", "Pending")))
        notes = st.text_area("Notes", value=existing.get("notes") or "")
        col1, col2 = st.columns(2)
        with col1:
            last_date = st.date_input("Last contacted", value=datetime.fromisoformat(existing_last.replace("Z", "+00:00")).date() if existing_last else None)
            last_time = st.time_input("Last contacted time", value=time(9, 0))
        with col2:
            follow_date = st.date_input("Next follow-up", value=datetime.fromisoformat(existing_follow_up.replace("Z", "+00:00")).date() if existing_follow_up else None)
            follow_time = st.time_input("Follow-up time", value=time(9, 0))
        saving = st.session_state.get("contact_save_in_progress", False)
        submitted = st.form_submit_button("Saving..." if saving else "Save contact", type="primary", disabled=saving)
    if not submitted:
        return None
    if not name.strip() or not purpose.strip():
        st.error("Name and purpose are required.")
        return None
    return {
        "name": name.strip(), "company": company.strip() or None, "email": email.strip() or None,
        "phone": phone.strip() or None, "purpose": purpose.strip(), "status": status,
        "notes": notes.strip() or None, "last_contacted_at": to_iso(last_date, last_time),
        "next_follow_up_at": to_iso(follow_date, follow_time),
    }


def dashboard_page() -> None:
    st.title("Follow-up desk")
    st.caption("A quiet place to keep important conversations moving.")
    summary = api_call(dashboard_summary)
    if summary is None:
        return
    metrics = [("All contacts", "total_contacts"), ("Pending", "pending_contacts"), ("Due today", "due_today"), ("Overdue", "overdue"), ("Replied", "replied_contacts"), ("Completed", "completed_contacts")]
    for row_start in range(0, len(metrics), 3):
        columns = st.columns(3)
        for column, (label, key) in zip(columns, metrics[row_start:row_start + 3]):
            column.metric(label, summary[key])
    st.subheader("Due today")
    due = api_call(follow_ups, "due")
    if due is not None:
        show_contacts(due)
    st.subheader("Overdue")
    overdue = api_call(follow_ups, "overdue")
    if overdue is not None:
        show_contacts(overdue)


def add_contact_page() -> None:
    st.title("Add contact")
    if st.session_state.pop("contact_saved_notice", False):
        st.success("Contact saved successfully. The form is ready for another contact.")
    payload = contact_form("new-contact")
    if payload is not None:
        st.session_state.setdefault("contact_submission_key", str(uuid.uuid4()))
        st.session_state["contact_save_in_progress"] = True
        with st.spinner("Saving contact..."):
            saved_contact = api_call(create_contact, payload, st.session_state["contact_submission_key"])
        if saved_contact is not None:
            st.session_state.pop("contact_save_in_progress", None)
            st.session_state.pop("contact_submission_key", None)
            st.session_state["contact_saved_notice"] = True
            st.session_state["new_contact_form_version"] = st.session_state.get("new_contact_form_version", 0) + 1
            st.rerun()
        st.session_state.pop("contact_save_in_progress", None)


def manage_contacts_page() -> None:
    st.title("Manage contacts")
    col1, col2, col3 = st.columns([2, 1, 1])
    search = col1.text_input("Search name or company")
    status = col2.selectbox("Status", ["All", "Pending", "Replied", "Completed", "No Response"])
    follow_up = col3.selectbox("Follow-up", ["All", "Due", "Overdue", "Upcoming", "Unscheduled"])
    page_size = st.selectbox("Rows per page", [10, 20, 50], index=1)
    page = st.number_input("Page", min_value=1, value=1, step=1)
    result = api_call(list_contacts, page=int(page), page_size=page_size, search=search, status="" if status == "All" else status, follow_up="" if follow_up == "All" else follow_up.lower())
    if result is None:
        return
    show_contacts(result["items"])
    if result["total"] > page_size:
        st.caption("Showing %s of %s contacts. Use the detail selector below to open any record." % (len(result["items"]), result["total"]))
    if result["items"]:
        choices = {"%s · %s" % (item["name"], item["company"] or "No company"): item["id"] for item in result["items"]}
        selected = st.selectbox("Open contact", ["Choose a contact"] + list(choices))
        if selected != "Choose a contact":
            st.session_state["selected_contact_id"] = choices[selected]
            st.rerun()
        st.subheader("Contact actions")
        for contact in result["items"]:
            with st.container(border=True):
                action_col, open_col, delete_col = st.columns([5, 1, 1])
                action_col.markdown("**%s**  \n%s · %s" % (contact["name"], contact.get("company") or "No company", contact["status"]))
                if open_col.button("Open", key="open_contact_%s" % contact["id"]):
                    st.session_state["selected_contact_id"] = contact["id"]
                    st.rerun()
                if delete_col.button("Delete", key="delete_contact_%s" % contact["id"], type="secondary"):
                    st.session_state["pending_delete_id"] = contact["id"]
                    st.rerun()
    pending_delete_id = st.session_state.get("pending_delete_id")
    if pending_delete_id:
        pending_contact = next((item for item in result["items"] if item["id"] == pending_delete_id), None)
        if pending_contact:
            st.warning("Delete %s? This permanently removes the contact and its interaction history." % pending_contact["name"])
            cancel_col, confirm_col = st.columns([1, 1])
            if cancel_col.button("Cancel deletion", key="cancel_delete"):
                st.session_state.pop("pending_delete_id", None)
                st.rerun()
            if confirm_col.button("Delete permanently", key="confirm_delete", type="secondary"):
                deleted = api_call(delete_contact, pending_delete_id)
                if deleted:
                    st.session_state.pop("pending_delete_id", None)
                    st.session_state["contact_deleted_notice"] = pending_contact["name"]
                    st.rerun()
        else:
            st.session_state.pop("pending_delete_id", None)
    if st.session_state.pop("contact_deleted_notice", None):
        st.success("Contact deleted successfully.")


def contact_detail_page(contact_id: int) -> None:
    contact = api_call(get_contact, contact_id)
    if contact is None:
        return
    st.title(contact["name"])
    st.caption("%s · %s" % (contact.get("company") or "Independent", contact["status"]))
    left, right = st.columns(2)
    with left:
        st.write("**Purpose**", contact["purpose"])
        st.write("**Email**", contact.get("email") or "Not provided")
        st.write("**Phone**", contact.get("phone") or "Not provided")
    with right:
        st.write("**Last contacted**", format_datetime(contact.get("last_contacted_at")))
        st.write("**Next follow-up**", format_datetime(contact.get("next_follow_up_at")))
        st.write("**Notes**", contact.get("notes") or "No notes")
    with st.expander("Edit contact", expanded=True):
        payload = contact_form("edit-contact", contact)
        if payload is not None:
            if api_call(update_contact, contact_id, payload) is not None:
                st.success("Contact updated.")
                st.rerun()
    st.subheader("Add interaction")
    with st.form("interaction"):
        interaction_type = st.selectbox("Type", ["Email", "Call", "Meeting", "Message", "Note"])
        interaction_date = st.date_input("Date")
        interaction_time = st.time_input("Time", value=time(9, 0))
        description = st.text_area("What happened?")
        outcome = st.text_input("Outcome")
        submitted = st.form_submit_button("Record interaction", type="primary")
    if submitted:
        if not description.strip():
            st.error("Add a short description before saving.")
        elif api_call(create_interaction, contact_id, {"interaction_type": interaction_type, "interaction_date": to_iso(interaction_date, interaction_time), "description": description.strip(), "outcome": outcome.strip() or None}) is not None:
            st.success("Interaction recorded.")
            st.rerun()
    st.subheader("Interaction history")
    for interaction in contact.get("interactions", []):
        st.markdown("**%s** · %s  \n%s%s" % (interaction["interaction_type"], format_datetime(interaction["interaction_date"]), interaction["description"], "  _" + interaction["outcome"] + "_" if interaction.get("outcome") else ""))
    st.divider()
    if st.button("Delete contact", type="secondary"):
        st.session_state["confirm_delete"] = True
    if st.session_state.get("confirm_delete"):
        st.warning("Deleting this contact also deletes its interaction history.")
        if st.button("Confirm deletion"):
            if api_call(delete_contact, contact_id) is None:
                return
            st.session_state.pop("selected_contact_id", None)
            st.session_state.pop("confirm_delete", None)
            st.success("Contact deleted.")
            st.rerun()


def follow_up_page() -> None:
    st.title("Follow-up center")
    tabs = st.tabs(["Due today", "Overdue", "Upcoming", "Unscheduled"])
    for tab, kind in zip(tabs, ["due", "overdue", "upcoming", "unscheduled"]):
        with tab:
            contacts = api_call(follow_ups, kind, 14) if kind == "upcoming" else api_call(follow_ups, kind)
            if contacts is None:
                continue
            show_contacts(contacts)
            if contacts:
                selection = st.selectbox("Open", ["Choose a contact"] + ["%s · %s" % (c["name"], c["id"]) for c in contacts], key="open_%s" % kind)
                if selection != "Choose a contact":
                    st.session_state["selected_contact_id"] = int(selection.rsplit("·", 1)[1])
                    st.rerun()


def main() -> None:
    st.sidebar.title("Smart Follow-Up")
    st.sidebar.caption("Conversation memory, made useful.")
    pages = ["Dashboard", "Add contact", "Manage contacts", "Follow-up center"]
    page = st.sidebar.radio("Navigate", pages)
    if st.session_state.get("selected_contact_id"):
        if st.sidebar.button("Back to contacts"):
            st.session_state.pop("selected_contact_id")
            st.rerun()
        contact_detail_page(st.session_state["selected_contact_id"])
    elif page == "Dashboard":
        dashboard_page()
    elif page == "Add contact":
        add_contact_page()
    elif page == "Manage contacts":
        manage_contacts_page()
    else:
        follow_up_page()


if __name__ == "__main__":
    main()
