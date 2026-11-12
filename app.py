from datetime import date

import pandas as pd
import streamlit as st

from placement_tracker_db import (
    APPLICATION_COLUMNS,
    add_application,
    applications_to_csv,
    delete_application,
    get_applications,
    get_most_applied_role,
    get_status_summary,
    get_total_applications,
    get_upcoming_interviews,
    initialize_database,
    update_application_status,
    update_interview_date,
)


STATUSES = [
    "Applied",
    "Shortlisted",
    "Interview Scheduled",
    "Selected",
    "Rejected",
]


st.set_page_config(page_title="Placement Application Tracker", page_icon="📋")
initialize_database()

st.title("Placement Application Tracker")
st.write("Track your job applications and monitor their progress.")

st.header("Add Application")
has_interview_date = st.checkbox("Add an interview date")

with st.form("add_application_form"):
    company_name = st.text_input("Company Name")
    job_role = st.text_input("Job Role")
    application_date = st.date_input("Application Date")
    status = st.selectbox("Status", STATUSES)
    interview_date = (
        st.date_input("Interview Date", min_value=date.today())
        if has_interview_date
        else None
    )
    add_button = st.form_submit_button("Add Application")

if add_button:
    company_name = company_name.strip()
    job_role = job_role.strip()

    if not company_name or not job_role:
        st.error("Company Name and Job Role cannot be empty.")
    else:
        add_application(
            company_name,
            job_role,
            application_date.isoformat(),
            status,
            interview_date.isoformat() if interview_date else None,
        )
        st.success("Application added successfully.")

st.header("Application Summary")
total_applications = get_total_applications()
most_applied_role = get_most_applied_role()

summary_column, role_column = st.columns(2)
summary_column.metric("Total Applications", total_applications)
role_column.metric(
    "Most Applied Role",
    most_applied_role if most_applied_role else "No applications yet",
)

st.header("Manage Applications")
all_applications = get_applications()

if all_applications:
    application_by_id = {row[0]: row for row in all_applications}
    application_ids = list(application_by_id)
    selected_id = st.selectbox(
        "Select an application",
        application_ids,
        format_func=lambda application_id: (
            f"{application_by_id[application_id][1]} — "
            f"{application_by_id[application_id][2]} "
            f"(ID {application_id})"
        ),
    )
    selected_application = application_by_id[selected_id]

    with st.form("update_status_form"):
        updated_status = st.selectbox(
            "Application Status",
            STATUSES,
            index=STATUSES.index(selected_application[4])
            if selected_application[4] in STATUSES
            else 0,
            key=f"status_{selected_id}",
        )
        update_status_button = st.form_submit_button("Update Status")

    if update_status_button:
        if update_application_status(selected_id, updated_status):
            st.success("Application status updated.")
        else:
            st.error("The selected application could not be found.")

    with st.form("update_interview_date_form"):
        current_interview_date = (
            date.fromisoformat(selected_application[5])
            if selected_application[5]
            else date.today()
        )
        updated_interview_date = st.date_input(
            "Interview Date",
            value=current_interview_date,
            key=f"interview_date_{selected_id}",
        )
        clear_interview_date = st.checkbox(
            "Clear interview date",
            value=False,
            key=f"clear_interview_date_{selected_id}",
        )
        update_interview_date_button = st.form_submit_button(
            "Save Interview Date"
        )

    if update_interview_date_button:
        new_interview_date = (
            None
            if clear_interview_date
            else updated_interview_date.isoformat()
        )
        if update_interview_date(selected_id, new_interview_date):
            st.success("Interview date updated.")
        else:
            st.error("The selected application could not be found.")

    confirm_delete = st.checkbox(
        "I confirm that I want to delete this application.",
        key=f"confirm_delete_{selected_id}",
    )
    if st.button("Delete Application", disabled=not confirm_delete):
        if delete_application(selected_id):
            st.success("Application deleted.")
        else:
            st.error("The selected application could not be found.")
else:
    st.info("Add an application to manage its status, interview date, or record.")

st.header("Upcoming Interviews")
upcoming_interviews = get_upcoming_interviews()
if upcoming_interviews:
    upcoming_table = pd.DataFrame(
        upcoming_interviews,
        columns=[
            "application_id",
            "company_name",
            "job_role",
            "interview_date",
        ],
    )
    st.dataframe(upcoming_table, use_container_width=True, hide_index=True)
else:
    st.info("No upcoming interviews scheduled.")

st.header("View Applications")
search_column, filter_column = st.columns(2)
company_query = search_column.text_input("Search by Company Name")
selected_status = filter_column.selectbox(
    "Filter by Status",
    ["All statuses", *STATUSES],
)
applications = get_applications(
    company_query=company_query,
    status=None if selected_status == "All statuses" else selected_status,
)

if applications:
    applications_table = pd.DataFrame(
        applications,
        columns=APPLICATION_COLUMNS,
    )
    st.dataframe(applications_table, use_container_width=True, hide_index=True)
    st.download_button(
        "Export displayed applications as CSV",
        data=applications_to_csv(applications),
        file_name="placement_applications.csv",
        mime="text/csv",
    )
else:
    st.info("No applications match the selected search and status filter.")

st.header("Status-wise Summary")
status_counts = get_status_summary(STATUSES)
status_table = pd.DataFrame(
    list(status_counts.items()),
    columns=["status", "application_count"],
)
st.dataframe(status_table, use_container_width=True, hide_index=True)
st.bar_chart(status_table.set_index("status"))
