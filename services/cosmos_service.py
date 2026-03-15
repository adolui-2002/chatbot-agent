import os
from azure.cosmos import CosmosClient
from dotenv import load_dotenv

load_dotenv()

client    = CosmosClient(os.getenv("COSMOS_ENDPOINT"), os.getenv("COSMOS_KEY"))
db        = client.get_database_client(os.getenv("COSMOS_DB"))
container = db.get_container_client(os.getenv("COSMOS_CONTAINER"))

# READ — get all subprojects under a super project
def get_subprojects(super_project_name: str):
    query = f"SELECT * FROM c WHERE c.super_project_name = '{super_project_name}'"
    return list(container.query_items(query, enable_cross_partition_query=True))

# READ — get one specific subproject
def get_project(super_project_name: str, project_name: str):
    query = f"""
        SELECT * FROM c
        WHERE c.super_project_name = '{super_project_name}'
        AND c.project_name = '{project_name}'
    """
    items = list(container.query_items(query, enable_cross_partition_query=True))
    return items[0] if items else None
# ── FIND by project_id first, fallback to project_name ──────
def find_project(search_term: str):

    # Step 1 — search by simple id (1, 2, 3...)
    query_by_id = "SELECT * FROM c WHERE c.id = @term"
    results = list(container.query_items(
        query=query_by_id,
        parameters=[{"name": "@term", "value": str(search_term)}],
        enable_cross_partition_query=True
    ))
    if results:
        return {"found_by": "id", "data": results[0]}

    # Step 2 — partial project_name match (case insensitive)
    query_by_name = """
        SELECT * FROM c
        WHERE CONTAINS(LOWER(c.project_name), LOWER(@term))
    """
    results = list(container.query_items(
        query=query_by_name,
        parameters=[{"name": "@term", "value": search_term.lower()}],
        enable_cross_partition_query=True
    ))
    if results:
        return {
            "found_by": "project_name",
            "data": results[0] if len(results) == 1 else results
        }

    # Step 3 — search inside project_details text
    query_by_details = """
        SELECT * FROM c
        WHERE CONTAINS(LOWER(c.project_details), LOWER(@term))
    """
    results = list(container.query_items(
        query=query_by_details,
        parameters=[{"name": "@term", "value": search_term.lower()}],
        enable_cross_partition_query=True
    ))
    if results:
        return {
            "found_by": "project_details",
            "data": results[0] if len(results) == 1 else results
        }

    return None
# UPDATE — update project details
def update_project_by_id(item_id: str, new_details: str):
    # Step 1 — READ by id
    query = "SELECT * FROM c WHERE c.id = @id"
    items = list(container.query_items(
        query=query,
        parameters=[{"name": "@id", "value": str(item_id)}],
        enable_cross_partition_query=True
    ))

    if not items:
        return None

    # Step 2 — MODIFY
    item = items[0]
    item["project_details"] = new_details

    # Step 3 — WRITE back (upsert = insert or update)
    container.upsert_item(item)
    return item
#ATE — add a new project
def create_project(data: dict):
    container.upsert_item(data)
    return data

# DELETE — remove a project
def delete_project(item_id: str, super_project_name: str):
    container.delete_item(item=item_id, partition_key=super_project_name)
    return {"deleted": item_id}