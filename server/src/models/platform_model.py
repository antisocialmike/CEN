from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

EntidadFederativa = Literal[
    "AGU", "BCN", "BCS", "CAM", "CHP", "CHH", "CMX", "COA",
    "COL", "DUR", "GUA", "GRO", "HID", "JAL", "MEX", "MIC",
    "MOR", "NAY", "NLE", "OAX", "PUE", "QUE", "ROO", "SLP",
    "SIN", "SON", "TAB", "TAM", "TLA", "VER", "YUC", "ZAC",
]

RFC_PATTERN = r"^[A-ZÑ&]{3,4}[0-9]{6}[A-Z0-9]{3}$"
REGISTRO_PATRONAL_PATTERN = r"^[A-Z][0-9]{10}$"


class CompanySummary(BaseModel):
    id: int
    legal_name: str
    is_active: bool


class OwnerSummary(BaseModel):
    id: int
    name: str
    is_active: bool


class Owner(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    companies: List[CompanySummary] = []


class OwnerCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=3, max_length=150)


class OwnerUpdateRequest(OwnerCreateRequest):
    pass


class OwnerCreatedResponse(BaseModel):
    owner: Owner
    temporary_password: str


class OwnerPasswordResetResponse(BaseModel):
    owner_id: int
    name: str
    email: str
    temporary_password: str


class CompanyAdmin(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    assigned_at: datetime


class CompanyBase(BaseModel):
    id: int
    legal_name: str
    trade_name: Optional[str] = None
    rfc: Optional[str] = None
    registro_patronal: Optional[str] = None
    entidad_federativa: Optional[EntidadFederativa] = None
    is_active: bool
    created_at: datetime


class Company(CompanyBase):
    owners: List[OwnerSummary] = []


class OwnerCompany(CompanyBase):
    admins: List[CompanyAdmin] = []


class CompanyData(BaseModel):
    legal_name: str = Field(min_length=1, max_length=200)
    trade_name: Optional[str] = Field(default=None, max_length=150)
    rfc: Optional[str] = Field(default=None, pattern=RFC_PATTERN)
    registro_patronal: Optional[str] = Field(
        default=None, pattern=REGISTRO_PATRONAL_PATTERN
    )
    entidad_federativa: Optional[EntidadFederativa] = None

    @field_validator(
        "trade_name", "rfc", "registro_patronal", "entidad_federativa",
        mode="before",
    )
    @classmethod
    def _blank_is_none(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("rfc", "registro_patronal", mode="before")
    @classmethod
    def _uppercase(cls, value):
        return value.strip().upper() if isinstance(value, str) else value


class CompanyCreateRequest(CompanyData):
    owner_id: int


class CompanyUpdateRequest(CompanyData):
    pass


class CompanyOwnerAssignRequest(BaseModel):
    owner_id: int


class AdminInviteRequest(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=3, max_length=150)


class AdminAssignRequest(BaseModel):
    email: str = Field(min_length=3, max_length=150)


class AdminInvitedResponse(BaseModel):
    company: OwnerCompany
    admin_id: int
    temporary_password: str
