## routers/client.py
from fastapi import APIRouter, HTTPException, Depends, status, Response
from sqlalchemy.orm import Session
from typing import List

from database.base import get_db
from database.models import User
from schemas.auth import UserOut
from schemas.clients import ClientCreate, ClientUpdate, ClientOut, ClientRemove
from services.clients import (
    get_clients_service,
    create_client_service,
    get_client_by_id_service,
    update_client_service,
    delete_client_service,
)
from utils.jwt import get_current_user, get_current_user_id_from_token

router = APIRouter()


# [auth] Add a new client and returns the client details
@router.post("/", response_model=ClientOut)
async def add_client(
    client_data: ClientCreate,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),
):
    try:
        created_client = create_client_service(
            db=db, client_data=client_data, current_user=current_user
        )
        return created_client
    except HTTPException as e:
        raise e
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create client.",
        )


# [auth,owner] Fetch clients the user has access to
@router.get("/", response_model=List[ClientOut])
async def fetch_clients(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: int = Depends(get_current_user_id_from_token),
):
    clients = get_clients_service(db, skip=skip, limit=limit)
    return clients


# [auth,owner] Fetch a single client based on the ID if the user has access
@router.get("/{client_id}", response_model=ClientOut)
async def fetch_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(get_current_user_id_from_token),
):
    db_client = get_client_by_id_service(db, client_id=client_id)
    if db_client is None:
        # This can mean "not found" or "access denied", 404 is appropriate for both to not leak info
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found or access denied",
        )
    return db_client


# [auth,owner] Update client details based on the ID if the user has access
@router.put("/{client_id}", response_model=ClientOut)
async def update_client_service_details(
    client_id: int,
    client_data: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),  # Get current user object
):
    try:
        updated_client = update_client_service(
            db=db,
            client_id=client_id,
            client_data=client_data,
            current_user=current_user,
        )
        if updated_client is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found or access denied for update",
            )
        return updated_client
    except HTTPException as e:
        raise e
    except Exception:  # Log the exception e
        # import logging
        # logging.error(f"Error updating client {client_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update client.",
        )


# [auth,owner] Remove a client based on the ID if the user has access
@router.delete("/{client_id}")
async def remove_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: UserOut = Depends(get_current_user),  # Get current user object
):
    deleted_client = delete_client_service(
        db=db, client_id=client_id, current_user=current_user
    )
    if deleted_client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found or access denied for deletion",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
