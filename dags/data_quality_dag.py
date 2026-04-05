from airflow import DAG

from dag_defaults import CORE_SCHEMA, DEFAULT_ARGS, STAGING_SCHEMA
from dataquality.soda import soda_scan_task

with DAG(
    dag_id="data_quality",
    default_args=DEFAULT_ARGS,
    description="SODA data quality checks on staging and core schemas",
    catchup=False,
    schedule=None,
) as dag:
    soda_validate_staging = soda_scan_task(STAGING_SCHEMA)
    soda_validate_core = soda_scan_task(CORE_SCHEMA)

    soda_validate_staging >> soda_validate_core
