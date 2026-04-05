import logging

from airflow.operators.bash import BashOperator

logger = logging.getLogger(__name__)

SODA_PATH = "/opt/airflow/include/soda"
DATASOURCE = "pg_datasource"


def soda_scan_task(schema: str):
    try:
        return BashOperator(
            task_id=f"soda_test_{schema}",
            bash_command=(
                f"soda scan -d {DATASOURCE} -c {SODA_PATH}/configuration.yml "
                f"-v SCHEMA={schema} {SODA_PATH}/checks.yml"
            ),
        )
    except Exception as e:
        logger.error("Error building SODA task for schema %s: %s", schema, e)
        raise
