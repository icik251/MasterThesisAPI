import motor.motor_asyncio

MONGO_IP = "192.168.239.134"
MONGO_URI = "mongodb://root:root@{}:27017".format(MONGO_IP)

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)

db = client.SP500_DB
company_collection = "company"

# def company_helper(company) -> dict:
#     return {
#         "id": str(company["_id"]),
#         "cik": company["cik"],
#         "name": company["name"],
#         "year": company["year"]
#     }

# Add a new company into to the database
async def add_company(company_data: dict) -> dict:
    company = await db[company_collection].insert_one(company_data)
    new_company = await db[company_collection].find_one({"_id": company.inserted_id})
    return new_company