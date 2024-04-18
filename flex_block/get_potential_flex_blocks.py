import pandas as pd


def get_potential_flex_blocks(blocks_df, queryStringParameters):
    blocks_df['start'] = pd.to_datetime(blocks_df['start'])
    blocks_df['end'] = pd.to_datetime(blocks_df['end'])
    blocks_df['day'] = blocks_df['start'].dt.date

    blocks_df['predicted_start'] = blocks_df['start']
    blocks_df['predicted_end'] = blocks_df['end'] - pd.to_timedelta(blocks_df['predicted_minutes_to_free_up'], unit='m')

    queryStringParameters['threshold_percentage'] = float(queryStringParameters.get('threshold_percentage', 0.95))
    queryStringParameters['threshold_abs'] = queryStringParameters.get('threshold_abs', 30)

    working_hours = {}

    blocks_df.sort_values(by=['day', 'resourceId', 'start'], inplace=True)
    blocks_df.groupby(['day', 'resourceId']).apply(
        get_potential_flex_blocks_in_room, queryStringParameters, working_hours
    )
    pass


def get_potential_flex_blocks_in_room(blocks_df, queryStringParameters, working_hours):
    blocks_df['left_gap'] = 0
    blocks_df['right_gap'] = 0
    if len(blocks_df) == 1:
        return blocks_df

    blocks_start = blocks_df['predicted_start'][1:].reset_index(drop=True)
    blocks_end = blocks_df['predicted_end'][:-1].reset_index(drop=True)
    gaps = (blocks_start - blocks_end).dt.total_seconds().div(60).astype(int)

    blocks_df.iloc[1:, 'left_gap'] = gaps
    pass


def is_potential_flex_block(block, queryStringParameters):
    pass
