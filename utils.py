import json
from datetime import datetime
from models import BlockModelFetched, OperationModelFetched


def filter_data(obj, whitelist):
    item = obj.to_dict()
    return {key: item[key] for key in whitelist if key in item}


def convert_dictionary_to_model(recordsArray):
    response_objects = []
    for item in recordsArray:
        if hasattr(item, 'allDay') and not hasattr(item, 'parent_block_id'):
            filtered_data = filter_data(item, whitelist=list(BlockModelFetched.__fields__.keys()))
            response_objects.append(BlockModelFetched(**filtered_data).to_dict())
        else:
            filtered_data = filter_data(item, whitelist=list(OperationModelFetched.__fields__.keys()))
            response_objects.append(OperationModelFetched(**filtered_data).to_dict())
    return response_objects


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
