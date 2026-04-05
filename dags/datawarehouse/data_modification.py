import logging

from datawarehouse.data_utils import TABLE_NAME

logger = logging.getLogger(__name__)


def insert_rows(cur, conn, schema, row):
    try:
        if schema == "staging":
            video_id = "video_id"
            cur.execute(
                f"""
                INSERT INTO {schema}.{TABLE_NAME}(
                    "Video_ID", "Video_Title", "Upload_Date", "Duration",
                    "Video_Views", "Likes_Count", "Comments_Count"
                )
                VALUES (
                    %(video_id)s, %(title)s, %(publishedAt)s, %(duration)s,
                    %(viewCount)s, %(likeCount)s, %(commentCount)s
                );
                """,
                row,
            )
        else:
            video_id = "Video_ID"
            cur.execute(
                f"""
                INSERT INTO {schema}.{TABLE_NAME}(
                    "Video_ID", "Video_Title", "Upload_Date", "Duration", "Video_Type",
                    "Video_Views", "Likes_Count", "Comments_Count"
                )
                VALUES (
                    %(Video_ID)s, %(Video_Title)s, %(Upload_Date)s, %(Duration)s, %(Video_Type)s,
                    %(Video_Views)s, %(Likes_Count)s, %(Comments_Count)s
                );
                """,
                row,
            )
        conn.commit()
        logger.info("Inserted row with Video_ID: %s", row[video_id])
    except Exception as e:
        logger.error("Error inserting row: %s", e)
        raise


def update_rows(cur, conn, schema, row):
    try:
        if schema == "staging":
            video_id = "video_id"
            upload_date = "publishedAt"
            video_title = "title"
            video_views = "viewCount"
            likes_count = "likeCount"
            comments_count = "commentCount"
        else:
            video_id = "Video_ID"
            upload_date = "Upload_Date"
            video_title = "Video_Title"
            video_views = "Video_Views"
            likes_count = "Likes_Count"
            comments_count = "Comments_Count"

        cur.execute(
            f"""
            UPDATE {schema}.{TABLE_NAME}
            SET "Video_Title" = %({video_title})s,
                "Video_Views" = %({video_views})s,
                "Likes_Count" = %({likes_count})s,
                "Comments_Count" = %({comments_count})s
            WHERE "Video_ID" = %({video_id})s AND "Upload_Date" = %({upload_date})s;
            """,
            row,
        )
        conn.commit()
        logger.info("Updated row with Video_ID: %s", row[video_id])
    except Exception as e:
        logger.error("Error updating row with Video_ID %s: %s", row.get(video_id), e)
        raise


def delete_rows(cur, conn, schema, ids_to_delete):
    try:
        id_list = f"""({', '.join(f"'{i}'" for i in ids_to_delete)})"""
        cur.execute(
            f"""
            DELETE FROM {schema}.{TABLE_NAME}
            WHERE "Video_ID" IN {id_list};
            """
        )
        conn.commit()
        logger.info("Deleted rows with Video_IDs: %s", id_list)
    except Exception as e:
        logger.error("Error deleting rows: %s", e)
        raise
