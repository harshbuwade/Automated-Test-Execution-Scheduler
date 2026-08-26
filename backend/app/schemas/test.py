from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.core.path_security import sanitize_and_validate_script_path
from app.models.enums import TestStatus


class TestCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Test suite name")
    description: Optional[str] = Field(None, max_length=2000, description="Test suite description")
    script_path: str = Field(..., description="Relative script path inside test_scripts directory")
    framework: str = Field("pytest", description="Test automation framework (default pytest)")
    timeout: int = Field(300, ge=1, le=3600, description="Timeout limit in seconds (1 to 3600)")
    status: TestStatus = Field(TestStatus.ACTIVE, description="Test status")

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Test name cannot be blank.")
        return cleaned

    @field_validator("script_path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        return sanitize_and_validate_script_path(v)

    @field_validator("framework")
    @classmethod
    def validate_framework(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if cleaned != "pytest":
            raise ValueError("Only 'pytest' framework is currently supported.")
        return cleaned


class TestUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    script_path: Optional[str] = Field(None)
    framework: Optional[str] = Field(None)
    timeout: Optional[int] = Field(None, ge=1, le=3600)
    status: Optional[TestStatus] = Field(None)

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Test name cannot be blank.")
            return cleaned
        return v

    @field_validator("script_path")
    @classmethod
    def validate_path(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return sanitize_and_validate_script_path(v)
        return v

    @field_validator("framework")
    @classmethod
    def validate_framework(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip().lower()
            if cleaned != "pytest":
                raise ValueError("Only 'pytest' framework is currently supported.")
            return cleaned
        return v


class TestResponse(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str] = None
    script_path: str
    framework: str
    timeout: int
    status: TestStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestListResponse(BaseModel):
    items: List[TestResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
