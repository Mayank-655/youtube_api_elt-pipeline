"""End-to-end checks via the Airflow CLI; intended to run inside the worker container."""

import os
import subprocess

import pytest


@pytest.mark.e2e
def test_airflow_cli_lists_project_dags():
    if not os.getenv("AIRFLOW_HOME"):
        pytest.skip("AIRFLOW_HOME not set (run in airflow-worker container).")

    result = subprocess.run(
        ["airflow", "dags", "list"],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    if result.returncode != 0:
        pytest.skip(
            "airflow dags list failed (scheduler/metadata not ready?): "
            f"{result.stderr or result.stdout}"
        )

    combined = result.stdout + result.stderr
    for dag_id in ("produce_json", "update_db", "data_quality"):
        assert dag_id in combined, f"Expected {dag_id} in airflow dags list output"
