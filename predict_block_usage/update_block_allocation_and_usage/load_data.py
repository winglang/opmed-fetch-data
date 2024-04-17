import os
from datetime import datetime

import pandas as pd

from predict_block_usage.utils.s3_utils import get_s3_object


def compute_scheduled_and_allocation_dfs(file_names):
    scheduled_dfs = []
    allocated_dfs = []
    counter = 0
    for file_name in file_names:
        counter += 1
        if counter % 50 == 0:
            print(f'file number {counter}')
        df = pd.DataFrame(get_s3_object(file_name, os.getenv('BUCKET_NAME_FETCH')))

        # get the date from file name
        file_date_str = file_name.split('.')[1][:8]  # Adjust slicing if necessary
        file_date = datetime.strptime(file_date_str, '%Y%m%d').date()
        df['start_date'] = pd.to_datetime(df['start']).dt.date

        # # Scheduled Usage:  # #
        # Filter rows where 'start_date' matches the date extracted from the file name
        rows_match_dates_df = df[df['start_date'] == file_date]
        scheduled_dfs.append(rows_match_dates_df)

        # # Original Allocations: # #
        # Remove rows for the last date in 'start', because it may be incomplete
        last_date_in_file = df['start_date'].max()
        df = df[df['start_date'] != last_date_in_file]
        last_complete_date_in_file = df['start_date'].max()

        # Filter rows with dates equal to
        rows_match_last_date = df[df['start_date'] == last_complete_date_in_file]
        allocated_dfs.append(rows_match_last_date)

        # Concatenate all filtered DataFrames
    scheduled_df = pd.concat(scheduled_dfs, ignore_index=True)
    allocated_df = pd.concat(allocated_dfs, ignore_index=True)
    varify_consecutive_dates(scheduled_df)  # todo: where do I raise a flag?
    varify_consecutive_dates(allocated_df)

    # compute total scheduled
    total_scheduled_time = compute_total_scheduled_time(scheduled_df)
    total_allocated_time = compute_total_allocation_time(allocated_df)

    return total_scheduled_time, total_allocated_time


def compute_total_scheduled_time(df):
    current_block_row_index = 0
    last_row_current_block = current_block_row_index + 1
    next_block_row_index = 0
    while next_block_row_index < len(df):
        while last_row_current_block < len(df) and pd.isna(df.loc[last_row_current_block, 'id']):
            last_row_current_block += 1
        next_block_row_index = last_row_current_block
        last_row_current_block = last_row_current_block - 1

        # now i know the first and last, I need to take the maximum and minimum and put it in the first row.
        df.loc[current_block_row_index, 'start'] = df.loc[
            current_block_row_index + 1 : last_row_current_block, 'start'
        ].min()
        df.loc[current_block_row_index, 'end'] = df.loc[
            current_block_row_index + 1 : last_row_current_block, 'end'
        ].max()

        current_block_row_index = next_block_row_index
        last_row_current_block = current_block_row_index + 1

    df_cleaned = df.dropna(subset=['id'])
    df_cleaned = df_cleaned.reset_index(drop=True)

    return df_cleaned


def compute_total_allocation_time(df):
    df_cleaned = df.dropna(subset=['id'])
    return df_cleaned


def varify_consecutive_dates(df):
    df['start'] = pd.to_datetime(df['start'])
    # Extract just the date part for easier comparison
    df['start_date'] = df['start'].dt.date
    # Identify the full range of dates in your DataFrame
    min_date = df['start_date'].min()
    max_date = df['start_date'].max()
    # Generate a complete list of dates in this range
    full_date_range = pd.date_range(start=min_date, end=max_date).date
    # Find which dates from the full range are not in your DataFrame
    missing_dates = set(full_date_range) - set(df['start_date'].unique())
    # Now, missing_dates contains all dates that are not represented in your DataFrame
    missing_dates = pd.to_datetime(list(missing_dates))
    missing_dates = missing_dates.sort_values()

    missing_dates.sort_values(ascending=True)
    # Iterate through each missing date
    for date in missing_dates:
        # Check if the day of the week is not Saturday
        if date.strftime('%A') != 'Saturday':
            # Print the date and the day of the week if it's not Saturday
            print(f"{date.date()} ({date.strftime('%A')})")
