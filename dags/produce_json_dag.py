from airflow import DAG
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

from api.video_stats import (
    extract_video_data,
    get_playlist_id,
    get_video_ids,
    save_to_json,
)
from dag_defaults import DEFAULT_ARGS

with DAG(
    dag_id="produce_json",
    default_args=DEFAULT_ARGS,
    description="DAG to produce JSON file with raw data",
    schedule="0 14 * * *",
    catchup=False,
) as dag:
    playlist_id = get_playlist_id()
    video_ids = get_video_ids(playlist_id)
    extract_data = extract_video_data(video_ids)
    save_to_json_task = save_to_json(extract_data)

    trigger_update_db = TriggerDagRunOperator(
        task_id="trigger_update_db",
        trigger_dag_id="update_db",
    )

    playlist_id >> video_ids >> extract_data >> save_to_json_task >> trigger_update_db
