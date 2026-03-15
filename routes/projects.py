from fastapi import APIRouter, HTTPException
from models.schemas import ProjectUpdate
from services.cosmos_service import (
    get_subprojects, get_project, update_project,
    create_project, delete_project, find_project
)

router = APIRouter()

@router.get("/projects/search/{search_term}")
def search_project(search_term: str):
    result = find_project(search_term)

    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No project found with id or name containing '{search_term}'"
        )

    return {
        "search_term": search_term,
        "found_by":    result["found_by"],   # tells you how it was found
        "result":      result["data"]
    }

# GET all subprojects of a super project
@router.get("/projects/{super_project_name}")
def list_projects(super_project_name: str):
    return get_subprojects(super_project_name)

# GET one specific subproject
@router.get("/projects/{super_project_name}/{project_name}")
def fetch_project(super_project_name: str, project_name: str):
    item = get_project(super_project_name, project_name)
    if not item:
        raise HTTPException(status_code=404, detail="Project not found")
    return item

# PUT update a project
@router.put("/projects/{super_project_name}/{project_name}")
def update(super_project_name: str, project_name: str, body: ProjectUpdate):
    updated = update_project(super_project_name, project_name, body.project_details)
    if not updated:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated

# POST create new project
@router.post("/projects")
def create(data: dict):
    return create_project(data)

# DELETE a project
@router.delete("/projects/{item_id}/{super_project_name}")
def delete(item_id: str, super_project_name: str):
    return delete_project(item_id, super_project_name)