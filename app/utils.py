import json
from bson import json_util
from bson.objectid import ObjectId

import json


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


def parse_model_to_dict(data):
    return json.loads(data.json())


def quarter_exist(company_db: dict, company_new: dict):
    for q_object in company_db["quarters"]:
        if company_new["quarter"] == q_object["quarter"]:
            return True

    return False

def verify_fundamental_data_features(curr_features_dict):
    size, zeros = True, True
    if len(curr_features_dict) != 19:
        size = False
    # means we have only 0
    if len(set(list(curr_features_dict.values()))) == 1:
       zeros = False
    
    return size, zeros
