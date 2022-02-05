import json
from bson import json_util
from bson.objectid import ObjectId


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


def parse_json(data):
    return json.loads(json_util.dumps(data))

def quarter_exist(company_db: dict, company_new: dict):
    for q_object in company_db['quarters']:
        if company_new['quarter'] == q_object['quarter']:
            return True
        
    return False
