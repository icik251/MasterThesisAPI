import motor.motor_asyncio
from bson.objectid import ObjectId

MONGO_URI = "mongodb://root:root@localhost:27017"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)

database = client.SP500_DB

company_collection = database.get_collection("company")

def company_helper(company) -> dict:
    return {
        "id": str(company["_id"]),
        "cik": company["cik"],
        "name": company["name"],
        "year": company["year"]
    }

# Add a new company into to the database
async def add_company(company_data: dict) -> dict:
    student = await company_collection.insert_one(company_data)
    new_student = await company_collection.find_one({"_id": student.inserted_id})
    return company_helper(new_student)