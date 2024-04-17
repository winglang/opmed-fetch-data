import os
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

from predict_block_usage.utils.constants import MORNING_START_TIME, MORNING_END_TIME
from predict_block_usage.update_block_allocation_and_usage.load_data import compute_scheduled_and_allocation_dfs
from predict_block_usage.utils.s3_utils import get_s3_object, get_delta_files_from_s3, put_item_in_s3

BUCKET_NAME_DB = None
BUCKET_NAME_FETCH = None
SCHEDULED_SURGERIES_DB_FILE_NAME = None
BLOCK_ALLOCATION_DB_FILE_NAME = None


def load_env():
    global BUCKET_NAME_DB, BUCKET_NAME_FETCH, SCHEDULED_SURGERIES_DB_FILE_NAME, BLOCK_ALLOCATION_DB_FILE_NAME
    load_dotenv()
    BUCKET_NAME_DB = os.getenv('BUCKET_NAME_DB')
    BUCKET_NAME_FETCH = os.getenv('BUCKET_NAME_FETCH')
    SCHEDULED_SURGERIES_DB_FILE_NAME = os.getenv('SCHEDULED_SURGERIES_DB_FILE_NAME')
    BLOCK_ALLOCATION_DB_FILE_NAME = os.getenv('BLOCK_ALLOCATION_DB_FILE_NAME')


def update_block_allocation_and_usage():
    load_env()
    scheduled_db, allocation_db, last_date = get_scheduled_and_allocation_dbs()

    # download files from s3 to local directory
    delta_file_names = get_delta_files_from_s3(
        bucket=BUCKET_NAME_FETCH,
        last_date=last_date,
        morning_start_time=MORNING_START_TIME,
        morning_end_time=MORNING_END_TIME,
    )

    delta_scheduled_df, delta_allocation_df = compute_scheduled_and_allocation_dfs(delta_file_names)

    df_scheduled_combined, df_allocation_combined = concat_delta_to_dbs(
        delta_scheduled_df, scheduled_db, delta_allocation_df, allocation_db
    )

    print('now uploading to s3')
    # upload to s3
    try:
        # Create a CSV string from the list of lists (CSV data)
        csv_scheduled_string = df_scheduled_combined.to_csv(index=False)
        csv_allocation_string = df_allocation_combined.to_csv(index=False)

        # Upload the CSV string to the specified file in the S3 bucket
        put_item_in_s3(bucket=BUCKET_NAME_DB, key=SCHEDULED_SURGERIES_DB_FILE_NAME, body=csv_scheduled_string)
        put_item_in_s3(bucket=BUCKET_NAME_DB, key=BLOCK_ALLOCATION_DB_FILE_NAME, body=csv_allocation_string)

    except Exception:  # noqa
        print('failed to upload to s3')


def concat_delta_to_dbs(delta_scheduled_df, scheduled_db, delta_allocation_df, allocation_db):
    if scheduled_db is not None:
        df_scheduled_combined = pd.concat([scheduled_db, delta_scheduled_df], ignore_index=True)
    else:
        df_scheduled_combined = delta_scheduled_df
    if allocation_db is not None:
        df_allocation_combined = pd.concat([allocation_db, delta_allocation_df], ignore_index=True)
    else:
        df_allocation_combined = delta_allocation_df

    df_scheduled_sorted = df_scheduled_combined.sort_values(by=['start', 'id'])
    df_allocated_sorted = df_allocation_combined.sort_values(by=['start', 'id'])
    return df_scheduled_sorted, df_allocated_sorted


def get_scheduled_and_allocation_dbs():
    scheduled_db = None
    allocation_db = None
    try:
        scheduled_db = get_s3_object(SCHEDULED_SURGERIES_DB_FILE_NAME, BUCKET_NAME_DB)
        allocation_db = get_s3_object(BLOCK_ALLOCATION_DB_FILE_NAME, BUCKET_NAME_DB)
        last_date = datetime.strptime(scheduled_db['start_date'].max(), '%Y-%m-%d')
    except Exception:  # noqa
        print('DBs do not exist, need to create new ones, returning default last date')
        last_date = datetime(year=2023, month=1, day=1)

    return scheduled_db, allocation_db, last_date


if __name__ == '__main__':
    update_block_allocation_and_usage()
