"""Postgres warehouse helpers: connections, DDL, and lookups."""

import os

from airflow.providers.postgres.hooks.postgres import PostgresHook
from psycopg2.extras import RealDictCursor

POSTGRES_CONN_ID = "postgres_db_yt_elt"
ELT_DATABASE_NAME = os.environ.get("ELT_DATABASE_NAME", "elt_db")
TABLE_NAME = "yt_api"


def get_conn_cursor():
    hook = PostgresHook(
        postgres_conn_id=POSTGRES_CONN_ID, database=ELT_DATABASE_NAME
    )
    conn = hook.get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    return conn, cur


def close_conn_cursor(conn, cur) -> None:
    if cur is not None:
        cur.close()
    if conn is not None:
        conn.close()


def create_schema(schema: str) -> None:
    conn, cur = get_conn_cursor()
    try:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")
        conn.commit()
    finally:
        close_conn_cursor(conn, cur)


def create_table(schema: str) -> None:
    conn, cur = get_conn_cursor()
    try:
        if schema == "staging":
            table_sql = f"""
            CREATE TABLE IF NOT EXISTS {schema}.{TABLE_NAME} (
                "Video_ID" VARCHAR(11) PRIMARY KEY NOT NULL,
                "Video_Title" TEXT NOT NULL,
                "Upload_Date" TIMESTAMP NOT NULL,
                "Duration" VARCHAR(20) NOT NULL,
                "Video_Views" INT,
                "Likes_Count" INT,
                "Comments_Count" INT
            );
            """
        else:
            table_sql = f"""
            CREATE TABLE IF NOT EXISTS {schema}.{TABLE_NAME} (
                "Video_ID" VARCHAR(11) PRIMARY KEY NOT NULL,
                "Video_Title" TEXT NOT NULL,
                "Upload_Date" TIMESTAMP NOT NULL,
                "Duration" TIME NOT NULL,
                "Video_Type" VARCHAR(10) NOT NULL,
                "Video_Views" INT,
                "Likes_Count" INT,
                "Comments_Count" INT
            );
            """
        cur.execute(table_sql)
        conn.commit()
    finally:
        close_conn_cursor(conn, cur)


def get_video_ids(cur, schema: str) -> list[str]:
    cur.execute(f"""SELECT "Video_ID" FROM {schema}.{TABLE_NAME};""")
    ids = cur.fetchall()
    return [row["Video_ID"] for row in ids]
