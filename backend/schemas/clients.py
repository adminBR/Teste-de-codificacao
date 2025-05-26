## schemas/client.py
from pydantic import BaseModel, EmailStr, constr, ConfigDict
from typing import Optional, Annotated
from datetime import datetime


# Shared properties
class ClientBase(BaseModel):
    cli_name: str
    cli_email: EmailStr
    cli_cpf: constr(min_length=11, max_length=11)


# Properties to return to client
class ClientOut(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    cli_id: int
    cli_created_at: datetime
    cli_updated_at: datetime
    cli_created_by: int


class ClientRemove(BaseModel):
    cli_id: int


# Properties to receive on client creation
class ClientCreate(ClientBase):
    pass


# Properties to receive on client update
class ClientUpdate(BaseModel):
    cli_name: Optional[str] = None
    cli_email: Optional[EmailStr] = None
    cli_cpf: constr(min_length=11, max_length=11) = None
