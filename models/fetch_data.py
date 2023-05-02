from datetime import datetime
from typing import Optional, List, Type, Union
from pydantic import BaseModel, validator


class TimeModel(BaseModel):
    id: int
    start: datetime
    end: datetime
    resourceId: str
    roomId: Optional[int]


class AdditionalResourceModel(BaseModel):
    monitor: bool
    x_ray: bool
    hospital_stretchers: bool
    defibrillators: bool
    anesthesia_machines: bool
    patient_monitors: bool
    sterilizers: bool
    ekg_machines: bool
    surgical_tables: bool
    blanket_and_fluid_warmers: bool
    tee: bool


class CurrentProcedureModel(BaseModel):
    side: str
    surgery_category: str
    surgery_name: str
    procedure: str
    surgery_duration: str
    procedure_code: str
    procedure_name: str
    procedure_icd: str


class ProcedureModel(BaseModel):
    current: List[CurrentProcedureModel]


class BlockModelFetched(TimeModel):
    id: int
    title: str
    nurse_name: Optional[str]
    sanitaire_name: Optional[str]
    assistant_name: Optional[str]
    anesthetist_name: Optional[str]
    doctor_name: str
    doctor_id: int
    doctors_license: str


class OperationModelFetched(TimeModel):
    parent_block_id: int
    surgery_id: int
    doc_name: str
    sur_name: str
    type: str
    procedure: ProcedureModel
    monitoring_request: Optional[str]
    xray_type: Optional[str]
    xray_type_value: Optional[str]
    tee_request: Optional[str]
    heart_lung_machine_request: Optional[str]
    additionalEquipment: Optional[AdditionalResourceModel]
    setup_time: int


class responseFetch(BaseModel):
    items: List[Union[BlockModelFetched, OperationModelFetched]]

    @classmethod
    @validator('items')
    def validate_root(cls, v):
        for item in v:
            if not isinstance(item, (BlockModelFetched, OperationModelFetched)):
                raise ValueError('List must only contain objects of type BlockModelFetched or OperationModelFetched')
        return v
