from models import BlockModelFetched, OperationModelFetched


def filter_data(item, whitelist):
    return {key: item[key] for key in whitelist if key in item}


def convert_dictionary_to_model(recordsArray):
    response_objects = []
    for item in recordsArray:
        if 'allDay' in item:
            filtered_data = filter_data(item, BlockModelFetched.swagger_types.keys())
            response_objects.append(BlockModelFetched(**filtered_data).to_dict())
        else:
            filtered_data = filter_data(item, OperationModelFetched.swagger_types.keys())
            response_objects.append(OperationModelFetched(**filtered_data).to_dict())
    return response_objects
