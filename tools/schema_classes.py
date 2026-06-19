from pydantic import BaseModel
from typing import Dict, List, Optional

class OndeField(BaseModel):
    full_name: str
    required: bool = False
    storage: Optional[str] = None
    hdf5_type: str
    description: str = ""
    short_description: Optional[str] = None
    dimensions: Optional[str] = None
    allowed_values: Optional[str] = None
    min_value: Optional[str] = None
    max_value: Optional[str] = None

class OndeClass(BaseModel):
    onde_class: str
    inherits: List[str] = []
    accessories: List[str] = []
    description: str = ""
    fields: Dict[str, OndeField] = {}

class OndeModality(BaseModel):
    modality: str
    description: str = ""
    allowed_classes: List[str] = []
    fields: Dict[str, OndeField] = {}
