from typing import Literal, Union, Optional, Annotated
from pydantic import BaseModel, Field, field_validator

class PersonARequest(BaseModel):
    user_type: Literal["person_a"]
    full_name: str
    age: int = Field(ge=18, le=70)
    gender: Literal["M", "F", "Other"]
    marital_status: Literal["Married", "Single"]
    education: Literal["Graduate", "Not Graduate"]
    self_employed: Literal["Yes", "No"]
    years_at_current_employer: int = Field(ge=0, le=50)
    annual_income: int = Field(ge=0)
    dependents: int = Field(ge=0, le=5)
    cibil_score: int
    loan_amount: int = Field(ge=300000)
    loan_term: int = Field(ge=2, le=20)
    loan_purpose: Literal["home", "education", "personal", "business", "vehicle", "medical"]
    residential_assets_value: int = Field(ge=0)
    commercial_assets_value: int = Field(ge=0)
    luxury_assets_value: int = Field(ge=0)
    bank_asset_value: int = Field(ge=0)

    @field_validator('cibil_score')
    @classmethod
    def validate_cibil_score(cls, v):
        if v not in (0, -1) and not (300 <= v <= 900):
            raise ValueError("CIBIL score must be 0, -1 or between 300 and 900.")
        return v

class PersonBRequest(BaseModel):
    user_type: Literal["person_b"]
    full_name: str
    age: int = Field(ge=18, le=70)
    gender: Literal["M", "F", "Other"]
    primary_business: str
    secondary_business: str
    annual_income: int = Field(ge=0)
    monthly_expenses: int = Field(ge=0)
    loan_amount: int = Field(ge=100)
    loan_purpose: str
    loan_tenure: int = Field(ge=1)
    loan_installments: int = Field(ge=1)
    young_dependents: int = Field(ge=0, le=15)
    old_dependents: int = Field(ge=0, le=10)
    occupants_count: int = Field(ge=1)
    home_ownership: int = Field(ge=0, le=1)
    type_of_house: Literal["pucca", "semi_pucca", "kucha", "T1", "T2", "R", "t1", "t2", "r"]
    house_area: Optional[int] = Field(None, ge=50)
    sanitary_availability: int = Field(ge=0, le=1)
    water_availability: Union[float, str]
    social_class: Optional[str] = None

    @field_validator('water_availability')
    @classmethod
    def validate_water(cls, v):
        if isinstance(v, str):
            if v.lower() not in ("none", "partial", "full"):
                raise ValueError("water_availability must be one of [0, 0.5, 1] or strings ['none', 'partial', 'full'].")
            return v.lower()
        if v not in (0.0, 0.5, 1.0):
            raise ValueError("water_availability must be one of [0, 0.5, 1] or strings ['none', 'partial', 'full'].")
        return v

UnifiedRequest = Annotated[Union[PersonARequest, PersonBRequest], Field(discriminator='user_type')]
