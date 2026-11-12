import os
import sqlite3
import tempfile
import unittest

from placement_tracker_db import (
    applications_to_csv,
    add_application,
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


class PlacementTrackerDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_name = os.path.join(self.temp_dir.name, "test.db")
        initialize_database(self.database_name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def add_application(self, company, role, status, interview_date=None):
        add_application(
            company,
            role,
            "2026-01-01",
            status,
            interview_date,
            self.database_name,
        )
        return get_applications(database_name=self.database_name)[-1][0]

    def test_existing_database_is_migrated_without_losing_records(self):
        legacy_database = os.path.join(self.temp_dir.name, "legacy.db")
        connection = sqlite3.connect(legacy_database)
        connection.execute(
            """
            CREATE TABLE applications (
                application_id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                job_role TEXT NOT NULL,
                application_date TEXT,
                status TEXT
            )
            """
        )
        connection.execute(
            """
            INSERT INTO applications
                (company_name, job_role, application_date, status)
            VALUES ('Acme', 'Engineer', '2026-01-01', 'Applied')
            """
        )
        connection.commit()
        connection.close()

        initialize_database(legacy_database)

        application = get_applications(database_name=legacy_database)[0]
        self.assertEqual(application[1:5], (
            "Acme",
            "Engineer",
            "2026-01-01",
            "Applied",
        ))
        self.assertIsNone(application[5])

    def test_company_search_is_case_insensitive_and_status_filter_works(self):
        self.add_application("Acme Systems", "Engineer", "Applied")
        self.add_application("Acme Labs", "Designer", "Shortlisted")
        self.add_application("Other Company", "Engineer", "Applied")

        results = get_applications(
            company_query="ACME",
            status="Shortlisted",
            database_name=self.database_name,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], "Acme Labs")

    def test_csv_export_contains_headers_and_filtered_records(self):
        self.add_application("Acme, Inc.", "Engineer", "Applied")

        results = get_applications(
            company_query="Acme",
            database_name=self.database_name,
        )
        exported = applications_to_csv(results).decode("utf-8")

        self.assertIn(
            "application_id,company_name,job_role,application_date,status,interview_date",
            exported,
        )
        self.assertIn('"Acme, Inc.",Engineer,2026-01-01,Applied,', exported)

    def test_status_and_interview_date_can_be_updated(self):
        application_id = self.add_application(
            "Acme",
            "Engineer",
            "Applied",
        )

        self.assertTrue(
            update_application_status(
                application_id,
                "Interview Scheduled",
                self.database_name,
            )
        )
        self.assertTrue(
            update_interview_date(
                application_id,
                "2026-12-01",
                self.database_name,
            )
        )

        application = get_applications(database_name=self.database_name)[0]
        self.assertEqual(application[4:], ("Interview Scheduled", "2026-12-01"))

    def test_upcoming_interviews_excludes_past_and_non_scheduled_records(self):
        self.add_application(
            "Future",
            "Engineer",
            "Interview Scheduled",
            "2026-11-20",
        )
        self.add_application(
            "Past",
            "Engineer",
            "Interview Scheduled",
            "2026-11-01",
        )
        self.add_application(
            "Not Scheduled",
            "Engineer",
            "Applied",
            "2026-11-25",
        )

        results = get_upcoming_interviews(
            today="2026-11-12",
            database_name=self.database_name,
        )

        self.assertEqual([row[1] for row in results], ["Future"])

    def test_application_can_be_deleted_and_summaries_update(self):
        first_id = self.add_application("Acme", "Engineer", "Applied")
        self.add_application("Beta", "Engineer", "Applied")

        self.assertTrue(delete_application(first_id, self.database_name))
        self.assertEqual(get_total_applications(self.database_name), 1)
        self.assertEqual(
            get_most_applied_role(self.database_name),
            "Engineer",
        )
        self.assertEqual(
            get_status_summary(
                ["Applied", "Rejected"],
                self.database_name,
            ),
            {"Applied": 1, "Rejected": 0},
        )


if __name__ == "__main__":
    unittest.main()
