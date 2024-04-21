import decimal
import json

import pandas as pd


class GeneralEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return int(o)
        if isinstance(o, pd.Timestamp):
            return o.isoformat()
        return super().default(o)
