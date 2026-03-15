import os
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Read credentials
ENDPOINT  = os.getenv("COSMOS_ENDPOINT")
KEY       = os.getenv("COSMOS_KEY")
DB_NAME   = os.getenv("COSMOS_DB")
CONTAINER = os.getenv("COSMOS_CONTAINER")

print("Connecting to:", ENDPOINT)

# Connect to Cosmos DB
client    = CosmosClient(ENDPOINT, KEY)
database  = client.get_database_client(DB_NAME)
container = database.get_container_client(CONTAINER)

# Try fetching first 3 records
print("\nFetching first 3 records...")
items = list(container.query_items(
    query="SELECT TOP 3 * FROM c",
    enable_cross_partition_query=True
))

for item in items:
    print(f"  ID: {item['id']} | Project: {item['project_name']} | Super: {item['super_project_name']}")

print("\nConnection successful!")