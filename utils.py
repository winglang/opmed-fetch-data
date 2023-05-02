import json
from datetime import datetime
from models import BlockModelFetched, OperationModelFetched


def filter_data(obj, whitelist):
    item = obj
    return {key: item[key] for key in whitelist if key in item}


def convert_dictionary_to_model(recordsArray):
    response_objects = []
    for item in recordsArray:
        if 'allDay' in item and 'parent_block_id' not in item:
            filtered_data = filter_data(item, whitelist=list(BlockModelFetched.__fields__.keys()))
            response_objects.append(BlockModelFetched(**filtered_data).dict())
        else:
            filtered_data = filter_data(item, whitelist=list(OperationModelFetched.__fields__.keys()))
            response_objects.append(OperationModelFetched(**filtered_data).dict())
    return response_objects


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
