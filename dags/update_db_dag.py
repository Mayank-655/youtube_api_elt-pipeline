from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

from dag_defaults import DEFAULT_ARGS
from datawarehouse.dwh import core_table, staging_table

with DAG(
    dag_id="update_db",
    default_args=DEFAULT_ARGS,
    description="Process JSON and load staging + core schemas",
    catchup=False,
    schedule=None,
) as dag:
    update_staging = staging_table()
    update_core = core_table()

    trigger_data_quality = TriggerDagRunOperator(
        task_id="trigger_data_quality",
        trigger_dag_id="data_quality",
    )

    update_staging >> update_core >> trigger_data_quality
