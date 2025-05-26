## services/clients.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from database.models import Client, User  # Import User model
from schemas.clients import ClientCreate, ClientUpdate, ClientOut
from schemas.auth import UserOut


## Only admins can create clients
## Checks for existing email or CPF to prevent duplicates.
## Create a single user
def create_client_service(
    db: Session, client_data: ClientCreate, current_user: UserOut
) -> Client:
    if not current_user.usr_isadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admins only."
        )

    existing_client_email = (
        db.query(Client).filter(Client.cli_email == client_data.cli_email).first()
    )
    if existing_client_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered."
        )

    existing_client_cpf = (
        db.query(Client).filter(Client.cli_cpf == client_data.cli_cpf).first()
    )
    if existing_client_cpf:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="CPF already registered."
        )

    db_client = Client(**client_data.model_dump(), cli_created_by=current_user.usr_id)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


## Any authenticated user
## Get a client based on the id
def get_client_by_id_service(db: Session, client_id: int) -> Client | None:
    return db.query(Client).filter(Client.cli_id == client_id).first()


## Any authenticated user
## Get all clients
def get_clients_service(db: Session, skip: int = 0, limit: int = 100) -> list[Client]:
    return db.query(Client).offset(skip).limit(limit).all()


## Only admins can update clients
## Checks for existing email or CPF to prevent duplicates.
## Update a client based on the id
def update_client_service(
    db: Session, client_id: int, client_data: ClientUpdate, current_user: UserOut
) -> Client | None:
    if not current_user.usr_isadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admins only."
        )

    db_client = db.query(Client).filter(Client.cli_id == client_id).first()
    if not db_client:
        return None

    update_data = client_data.model_dump(exclude_unset=True)

    if "cli_email" in update_data and update_data["cli_email"] != db_client.cli_email:
        existing_client_email = ClientOut.model_validate(
            db.query(Client)
            .filter(Client.cli_email == update_data["cli_email"])
            .first()
        )
        if existing_client_email and existing_client_email.cli_id != client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered by another client.",
            )

    if "cli_cpf" in update_data and update_data["cli_cpf"] != db_client.cli_cpf:
        existing_client_cpf = ClientOut.model_validate(
            db.query(Client).filter(Client.cli_cpf == update_data["cli_cpf"]).first()
        )
        if existing_client_cpf and existing_client_cpf.cli_id != client_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CPF already registered by another client.",
            )

    for key, value in update_data.items():
        setattr(db_client, key, value)

    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


## Only admins can delete clients
## Delete a client based on the id
def delete_client_service(
    db: Session, client_id: int, current_user: UserOut
) -> Client | None:
    if not current_user.usr_isadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admins only."
        )

    db_client = db.query(Client).filter(Client.cli_id == client_id).first()
    if not db_client:
        return None

    db.delete(db_client)
    db.commit()
    return db_client
