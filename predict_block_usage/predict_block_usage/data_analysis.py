import json
from datetime import timedelta
import pandas as pd

from predict_block_usage.utils.s3_utils import get_s3_object


def compute_records_and_averages(df, DOCTORS_TO_HASH_FILE_NAME, BUCKET_NAME_DB):

    df_1W_bins = compute_xW_bins(df.copy(deep=True), 1, DOCTORS_TO_HASH_FILE_NAME, BUCKET_NAME_DB)
    df_4W_bins = compute_xW_bins(df.copy(deep=True), 4, DOCTORS_TO_HASH_FILE_NAME, BUCKET_NAME_DB)
    dict_average = compute_averages_dict(df_4W_bins)
    return compute_json_for_s3(df_1W_bins, df_4W_bins, dict_average)


def save_to_json(all_surgeons_data, json_file_name):
    # Convert the all_surgeons_data dictionary to JSON
    json_data = json.dumps(all_surgeons_data, indent=4, default=str)
    # Define the filename for the JSON file
    # Save the JSON data to a file
    with open(json_file_name, 'w') as file:
        file.write(json_data)
    print(f"Data successfully saved to {json_file_name}")


def compute_xW_bins(df, weeks, DOCTORS_TO_HASH_FILE_NAME, BUCKET_NAME_DB):
    df_bins = split_to_xW_bins(df, weeks)
    # sort df_bins by surgeons_id
    df_bins = df_bins.sort_values(by=['doctors_license', 'start'])
    df_bins = df_bins.rename(columns={'doctors_license': 'merge_id'})
    df_bins = df_bins.rename(columns={'start': 'date'})

    df_doctors_to_hash = get_s3_object(DOCTORS_TO_HASH_FILE_NAME, BUCKET_NAME_DB)
    df_doctors_to_hash = df_doctors_to_hash.rename(columns={'original_id': 'merge_id'})
    df_doctors_to_hash = df_doctors_to_hash.rename(columns={'id': 'hash'})

    df_bins_merged = pd.merge(df_bins, df_doctors_to_hash[['merge_id', 'hash']], on='merge_id', how='left')
    final_df = df_bins_merged.drop('merge_id', axis=1)

    # turn duration into hours
    final_df['duration_sum'] = round(final_df['duration_sum'] / 60, 2)

    return final_df


def split_to_xW_bins(df_input, weeks):
    df = df_input.copy(deep=True)
    # Convert the 'planned_start' column to datetime format if it's not already
    df['start'] = pd.to_datetime(df['start'])
    df['end'] = pd.to_datetime(df['end'])
    df['duration'] = (df['end'] - df['start']).dt.total_seconds() / 60
    df['date'] = df['start'].dt.date

    # make col the forth column
    cols = [col for col in df.columns if col != 'duration']
    cols.insert(3, 'duration')
    df = df[cols]

    # #  make sure the last bin is full, delete the first bin
    # min_date = df['start'].min()
    # max_date = df['start'].max()
    # date_diff = max_date - min_date
    # num_days = date_diff.days
    # days_to_trim = num_days % (7 * 4)
    # min_date = min_date + pd.Timedelta(days=days_to_trim)
    # df = df[df['start'] >= min_date]

    # Group the data by 'surgeon_index' and weeks-week periods, and sum the durations
    freq_str = str(weeks) + 'W'
    # Group the DataFrame and perform the aggregation
    df_grouped = df.groupby(['doctors_license', pd.Grouper(key='start', freq=freq_str)]).agg(
        duration_sum=('duration', 'sum'),  # Sum the duration for each group
        row_count=('duration', 'size')  # Count the rows in each group
    ).reset_index()

    # remove the last bin for every doctor
    df_grouped = df_grouped.groupby('doctors_license').apply(lambda x: x.iloc[:-1]).reset_index(drop=True)

    # The 'start' column now contains the start of each bin due to the reset_index
    # Calculate the last date of the bin by adding 4 weeks and subtracting 1 day
    df_grouped['last_date'] = df_grouped['start']
    df_grouped['first_date'] = df_grouped['start'] - pd.Timedelta(weeks=weeks) + pd.Timedelta(days=1)

    # Convert datetime to date to remove the time component
    df_grouped['first_date'] = df_grouped['first_date'].dt.date
    df_grouped['last_date'] = df_grouped['last_date'].dt.date

    # Combine into a tuple and ensure only the date part is considered
    df_grouped['dates'] = df_grouped.apply(lambda row: (row['first_date'], row['last_date']), axis=1)

    return df_grouped


def test_compute_4_week_bins(df_input, weeks):
    """
    Groups the DataFrame by doctor's license, computes 4-week bins, and fills empty bins with a duration of 0.

    Parameters:
    - df: DataFrame containing at least 'doctors_license', 'start', and 'duration' columns.
    - weeks: The number of weeks to define each bin. Default is 4 weeks.

    Returns:
    - A DataFrame with each doctor's license, the start of each 4-week bin, and the sum of durations within each bin.
      Empty bins will have a duration of 0.
    """
    df = df_input.copy()
    df['start'] = pd.to_datetime(df['start'])
    df['end'] = pd.to_datetime(df['end'])
    df['duration'] = (df['end'] - df['start']).dt.total_seconds() / 60
    df['date'] = df['start'].dt.date

    # make col the forth column
    cols = [col for col in df.columns if col != 'duration']
    cols.insert(3, 'duration')
    df = df[cols]

    #  make sure the last bin is full, delete the first bin
    min_date = df['start'].min()
    max_date = df['start'].max()
    date_diff = max_date - min_date
    num_days = date_diff.days
    days_to_trim = num_days % (7 * 4)
    min_date = min_date + pd.Timedelta(days=days_to_trim)
    df = df[df['start'] >= min_date]
    # Ensure 'start' is a datetime column
    df['start'] = pd.to_datetime(df['start'])

    # Define the frequency string based on the number of weeks
    freq_str = str(weeks) + 'W'

    # Create a new DataFrame to store results
    result_df = pd.DataFrame()

    # Group by 'doctors_license'
    grouped = df.groupby('doctors_license')

    for name, group in grouped:
        # Set 'start' as the index for resampling
        group.set_index('start', inplace=True)

        # Resample to sum durations within each bin
        resampled = group['duration'].resample(freq_str).sum()

        # Generate a complete index of 4-week bins within the range of the group's dates
        period_range = pd.date_range(start=resampled.index.min(), end=resampled.index.max(), freq=freq_str)

        # Reindex the resampled DataFrame to include all periods, filling missing ones with zeros
        reindexed = resampled.reindex(period_range, fill_value=0)

        # Convert index (start of each bin) back to a column and add the doctor's license
        reindexed_df = reindexed.reset_index()
        reindexed_df['doctors_license'] = name

        # Append to the result DataFrame
        result_df = pd.concat([result_df, reindexed_df])

    # Rename columns for clarity
    result_df.rename(columns={'index': 'bin_start', 0: 'duration_sum'}, inplace=True)

    # Reset index of the final DataFrame
    result_df.reset_index(drop=True, inplace=True)

    return result_df


def compute_averages_dict(df):
    # df['date'] = pd.to_datetime(df['date'])
    df.sort_values(by=['hash', 'date'], inplace=True)

    surgeons_dict = {}

    # Define periods in weeks
    periods = {'last_four_weeks_average': 4, 'last_quarter_average': 12, 'last_year_average': 52}

    # Loop through each surgeon
    for surgeon_hash in df['hash'].unique():
        surgeon_data = df[df['hash'] == surgeon_hash]
        surgeon_dict = {}

        # Get the last date for the current surgeon to calculate periods from
        last_date = surgeon_data['date'].max()

        for period_name, weeks in periods.items():
            # Calculate the start date for the period
            period_start_date = last_date - timedelta(weeks=weeks)

            # Filter the data for this period
            period_data = surgeon_data[(surgeon_data['date'] > period_start_date) & (surgeon_data['date'] <= last_date)]

            # Check if there are enough data points for the period
            if len(period_data) == weeks / 4:
                # Calculate the average and update the surgeon's dictionary
                surgeon_dict[period_name] = round(period_data['duration_sum'].mean(), 2)
            else:
                # Not enough data for the period, set to -1
                surgeon_dict[period_name] = -1

        # Update the main dictionary
        surgeons_dict[surgeon_hash] = surgeon_dict

    # The surgeons_dict now contains the required information
    return surgeons_dict


def compute_json_for_s3(df_1W, df_4W, surgeons_dict):
    # Ensure 'date' is in the correct format and sort df
    for df in [df_1W, df_4W]:
        df['date'] = pd.to_datetime(df['date'])
        df.sort_values(by=['hash', 'date'], inplace=True)

    # Initialize a dictionary to hold all combined information
    all_surgeons_data = {}

    # Iterate through each unique surgeon hash
    for surgeon_hash in df_1W['hash'].unique():
        surgeon_records = {}

        surgeon_1W_df = df_1W[df_1W['hash'] == surgeon_hash]
        surgeon_4W_df = df_4W[df_4W['hash'] == surgeon_hash]

        surgeon_records['one_week'] = surgeon_1W_df.to_dict(orient='records')
        surgeon_records['four_weeks'] = surgeon_4W_df.to_dict(orient='records')

        # Get the averages data from surgeons_dict for the current surgeon
        averages_data = surgeons_dict.get(surgeon_hash, {})

        # Combine DataFrame data and averages data
        all_surgeons_data[surgeon_hash] = {
            'records': surgeon_records,
            'averages': averages_data
        }

    return all_surgeons_data
