import json
import os

from dotenv import load_dotenv

from predict_block_usage.predict_block_usage.data_analysis import compute_records_and_averages
from predict_block_usage.utils.s3_utils import get_s3_object, put_item_in_s3

SCHEDULED_SURGERIES_DB_FILE_NAME = None
BUCKET_NAME_DB = None
BUCKET_NAME_PREDICTqIONS_OUTPUT = None
PREDICTIONS_OUTPUT_FILE_NAME = None
DOCTORS_TO_HASH_FILE_NAME = None


def load_env():
    global \
        BUCKET_NAME_DB, \
        SCHEDULED_SURGERIES_DB_FILE_NAME, \
        BUCKET_NAME_PREDICTIONS_OUTPUT, \
        PREDICTIONS_OUTPUT_FILE_NAME, \
        DOCTORS_TO_HASH_FILE_NAME
    load_dotenv()
    BUCKET_NAME_DB = os.getenv('BUCKET_NAME_DB')
    SCHEDULED_SURGERIES_DB_FILE_NAME = os.getenv('SCHEDULED_SURGERIES_DB_FILE_NAME')
    BUCKET_NAME_PREDICTIONS_OUTPUT = os.getenv('BUCKET_NAME_PREDICTIONS_OUTPUT')
    PREDICTIONS_OUTPUT_FILE_NAME = os.getenv('PREDICTIONS_OUTPUT_FILE_NAME')
    DOCTORS_TO_HASH_FILE_NAME = os.getenv('DOCTORS_TO_HASH_FILE_NAME')


def predict_block_usage():
    load_env()
    # # # Compute bins # # #
    df_schedule = get_s3_object(SCHEDULED_SURGERIES_DB_FILE_NAME, BUCKET_NAME_DB)
    all_surgeons_data = compute_records_and_averages(df_schedule, DOCTORS_TO_HASH_FILE_NAME, BUCKET_NAME_DB)
    # file path is block name, file name
    json_data = json.dumps(all_surgeons_data, indent=4, default=str)
    put_item_in_s3(
        bucket=BUCKET_NAME_PREDICTIONS_OUTPUT, key=PREDICTIONS_OUTPUT_FILE_NAME, body=json_data, acl_needed=True
    )


if __name__ == '__main__':
    predict_block_usage()
