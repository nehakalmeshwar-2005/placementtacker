import sqlite3

import pandas as pd
import streamlit as st


DATABASE_NAME = "placements.db"
STATUSES = [
    "Applied",
    "Shortlisted",
    "Interview Scheduled",
    "Selected",
    "Rejected",
]


def get_connection():
    """Open a connection to the SQLite database."""
    return sqlite3.connect(DATABASE_NAME)


def add_application(company_name, job_role, application_date, status):
    """Save one application in the database."""
    connection = get_connection()
    connection.execute(
        """
        INSERT INTO applications
            (company_name, job_role, application_date, status)
        VALUES (?, ?, ?, ?)
        """,
        (company_name, job_role, application_date, status),
    )
    connection.commit()
    connection.close()


def get_applications():
    """Retrieve all applications from the database."""
    connection = get_connection()
    applications = connection.execute(
        """
        SELECT application_id, company_name, job_role,
               application_date, status
        FROM applications
        ORDER BY application_id
        """
    ).fetchall()
    connection.close()
    return applications


def get_total_applications():
    """Return the number of saved applications."""
    connection = get_connection()
    total = connection.execute(
        "SELECT COUNT(*) FROM applications"
    ).fetchone()[0]
    connection.close()
    return total


def get_most_applied_role():
    """Return the most frequently used job role.

    If roles are tied, the role that comes first alphabetically is returned.
    """
    connection = get_connection()
    result = connection.execute(
        """
        SELECT job_role, COUNT(*) AS application_count
        FROM applications
        GROUP BY job_role
        ORDER BY application_count DESC, job_role ASC
        LIMIT 1
        """
    ).fetchone()
    connection.close()
    return result[0] if result else None


def get_status_summary():
    """Return application counts for every available status."""
    connection = get_connection()
    rows = connection.execute(
        """
        SELECT status, COUNT(*) AS application_count
        FROM applications
        GROUP BY status
        """
    ).fetchall()
    connection.close()

    counts = {status: 0 for status in STATUSES}
    for status, count in rows:
        if status in counts:
            counts[status] = count
    return counts


st.set_page_config(page_title="Placement Application Tracker", page_icon="📋")
st.title("Placement Application Tracker")
st.write("Track your job applications and monitor their progress.")

st.header("Add Application")

with st.form("add_application_form"):
    company_name = st.text_input("Company Name")
    job_role = st.text_input("Job Role")
    application_date = st.date_input("Application Date")
    status = st.selectbox("Status", STATUSES)
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

st.header("View Applications")
applications = get_applications()

if applications:
    applications_table = pd.DataFrame(
        applications,
        columns=[
            "application_id",
            "company_name",
            "job_role",
            "application_date",
            "status",
        ],
    )
    st.dataframe(applications_table, use_container_width=True, hide_index=True)
else:
    st.info("No applications available yet.")

st.header("Status-wise Summary")
status_counts = get_status_summary()
status_table = pd.DataFrame(
    list(status_counts.items()),
    columns=["status", "application_count"],
)
st.dataframe(status_table, use_container_width=True, hide_index=True)
st.bar_chart(status_table.set_index("status"))
