import pandas as pd

from utils.api_utils import get_tenant_params, get_blocks_predictions

FLEX_BLOCK_RESPONSE_FIELDS = pd.Series(
    [
        'start',
        'end',
        'duration',
        'predicted_start',
        'predicted_end',
        'predicted_duration',
        'left_gap',
        'right_gap',
        'room',
        'doctor_id',
        'block_id',
        'doctors_license',
    ]
)


def get_potential_flex_blocks(fetch_data, headers):
    try:
        blocks_predictions_res = get_blocks_predictions(fetch_data, headers)

        predicted_blocks = blocks_predictions_res['body']
        blocks_df = pd.DataFrame(predicted_blocks)

        blocks_df['block_id'] = blocks_df['id']
        blocks_df['start'] = pd.to_datetime(blocks_df['start'])
        blocks_df['end'] = pd.to_datetime(blocks_df['end'])
        blocks_df['day'] = blocks_df['start'].dt.floor('d')

        blocks_df['predicted_start'] = blocks_df['start']
        blocks_df['predicted_end'] = blocks_df['end'] - pd.to_timedelta(
            blocks_df['predicted_minutes_to_free_up'], unit='m'
        )
        blocks_df['predicted_duration'] = blocks_df['duration'] - blocks_df['predicted_minutes_to_free_up']

        working_hours = get_tenant_params(headers).get('working_hours', {})['days']

        blocks_df.sort_values(by=['day', 'resourceId', 'start'], inplace=True)
        blocks_df = blocks_df.groupby(['day', 'resourceId']).apply(get_adjacent_gaps, working_hours)
        blocks_df.set_index('id', inplace=True)

        blocks_df = blocks_df[FLEX_BLOCK_RESPONSE_FIELDS[FLEX_BLOCK_RESPONSE_FIELDS.isin(blocks_df.columns)]]

        return {'statusCode': 200, 'body': blocks_df.to_dict(orient='records')}
    except Exception as e:
        return {'statusCode': 500, 'error': str(e)}


def get_adjacent_gaps(blocks_df, working_hours):
    blocks_df['left_gap'] = 0
    blocks_df['right_gap'] = 0
    if len(blocks_df) == 1:
        return blocks_df

    day = blocks_df['day'].iloc[0].strftime('%A')
    working_hours = working_hours[day][0]
    working_hours_start_time = pd.to_timedelta(pd.to_datetime(working_hours['startTime']).strftime('%H:%M:%S'))
    working_hours_end_time = working_hours_start_time + pd.to_timedelta(working_hours['durationMinutes'], unit='m')

    start_of_day = blocks_df.iloc[0]['day'] + working_hours_start_time
    end_of_day = blocks_df.iloc[0]['day'] + working_hours_end_time

    blocks_start = pd.concat([blocks_df.predicted_start, pd.Series(end_of_day)], ignore_index=True)
    blocks_end = pd.concat([pd.Series(start_of_day), blocks_df.predicted_end], ignore_index=True)

    gaps = (blocks_start - blocks_end).dt.total_seconds().div(60).astype(int)

    blocks_df['left_gap'] = gaps[:-1].tolist()
    blocks_df['right_gap'] = gaps[1:].tolist()
    return blocks_df
