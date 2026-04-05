"""Shared default arguments and schema names for Airflow DAGs."""

from datetime import datetime, timedelta

import pendulum

LOCAL_TZ = pendulum.timezone("Europe/Malta")

DEFAULT_ARGS = {
    "owner": "dataengineers",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "email": "data@engineers.com",
    "max_active_runs": 1,
    "dagrun_timeout": timedelta(hours=1),
    "start_date": datetime(2025, 1, 1, tzinfo=LOCAL_TZ),
}

STAGING_SCHEMA = "staging"
CORE_SCHEMA = "core"
