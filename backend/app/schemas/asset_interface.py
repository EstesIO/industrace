from pydantic import BaseModel, Field, ConfigDict, validator
from typing import Optional, Dict, List
from datetime import datetime
from uuid import UUID
from app.schemas.validators import *


class AssetInterfaceBase(BaseModel):
    name: Optional[str] = Field(None, max_length=50, description="Interface name")
    type: Optional[str] = Field(None, max_length=50, description="Interface type")
    vlan: Optional[str] = Field(None, max_length=50, description="VLAN")
    logical_port: Optional[str] = Field(None, max_length=100, description="Logical port")
    physical_plug_label: Optional[str] = Field(None, max_length=100, description="Physical plug label")
    details: Optional[Dict] = Field(default_factory=dict)
    ip_address: Optional[str] = Field(None, max_length=50, description="IP address")
    subnet_mask: Optional[str] = Field(None, max_length=50, description="Subnet mask")
    default_gateway: Optional[str] = Field(None, max_length=50, description="Default gateway")
    mac_address: Optional[str] = Field(None, max_length=50, description="MAC address")
    other: Optional[str] = Field(None, max_length=255, description="Other information")
    protocols: Optional[List[str]] = Field(default_factory=list, description="Industrial protocols supported by this interface")

    # Validators
    _validate_ip_address = validator('ip_address', allow_reuse=True)(validate_ip_address)
    _validate_mac_address = validator('mac_address', allow_reuse=True)(validate_mac_address)
    _validate_vlan = validator('vlan', allow_reuse=True)(validate_vlan)


class AssetInterfaceCreate(AssetInterfaceBase):
    asset_id: UUID
    tenant_id: UUID


class AssetInterfaceUpdate(AssetInterfaceBase):
    id: Optional[UUID] = None


class AssetInterface(AssetInterfaceBase):
    id: UUID
    asset_id: UUID
    tenant_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
