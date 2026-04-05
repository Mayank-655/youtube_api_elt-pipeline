import logging

from airflow.decorators import task

from datawarehouse.data_loading import load_data
from datawarehouse.data_modification import delete_rows, insert_rows, update_rows
from datawarehouse.data_transformation import transform_data
from datawarehouse.data_utils import (
    TABLE_NAME,
    close_conn_cursor,
    create_schema,
    create_table,
    get_conn_cursor,
    get_video_ids,
)

logger = logging.getLogger(__name__)


@task
def staging_table():
    schema = "staging"
    conn, cur = None, None
    try:
        conn, cur = get_conn_cursor()
        yt_data = load_data()
        create_schema(schema)
        create_table(schema)
        table_ids = get_video_ids(cur, schema)
        initial_load = len(table_ids) == 0

        for row in yt_data:
            if initial_load:
                insert_rows(cur, conn, schema, row)
            elif row["video_id"] in table_ids:
                update_rows(cur, conn, schema, row)
            else:
                insert_rows(cur, conn, schema, row)

        ids_in_json = {row["video_id"] for row in yt_data}
        ids_to_delete = set(table_ids) - ids_in_json
        if ids_to_delete:
            delete_rows(cur, conn, schema, ids_to_delete)

        logger.info("%s table update completed", schema)
    except Exception as e:
        logger.error("Error updating %s table: %s", schema, e)
        raise
    finally:
        if conn is not None and cur is not None:
            close_conn_cursor(conn, cur)


@task
def core_table():
    schema = "core"
    conn, cur = None, None
    try:
        conn, cur = get_conn_cursor()
        create_schema(schema)
        create_table(schema)
        table_ids = get_video_ids(cur, schema)
        initial_load = len(table_ids) == 0
        current_video_ids = set()

        cur.execute(f"SELECT * FROM staging.{TABLE_NAME};")
        rows = cur.fetchall()

        for row in rows:
            current_video_ids.add(row["Video_ID"])
            transformed_row = transform_data(dict(row))

            if initial_load:
                insert_rows(cur, conn, schema, transformed_row)
            elif transformed_row["Video_ID"] in table_ids:
                update_rows(cur, conn, schema, transformed_row)
            else:
                insert_rows(cur, conn, schema, transformed_row)

        ids_to_delete = set(table_ids) - current_video_ids
        if ids_to_delete:
            delete_rows(cur, conn, schema, ids_to_delete)

        logger.info("%s table update completed", schema)
    except Exception as e:
        logger.error("Error updating %s table: %s", schema, e)
        raise
    finally:
        if conn is not None and cur is not None:
            close_conn_cursor(conn, cur)
