from datetime import datetime
from typing import Optional, List, Union, Literal

from pydantic import BaseModel, validator


class TimeModel(BaseModel):
    id: Optional[str]
    start: datetime
    end: datetime
    resourceId: str
    roomId: Optional[str]


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
    side: Union[str, None]
    surgery_category: Union[str, None]
    surgery_name: str
    procedure: Optional[str] = ''
    surgery_duration: str
    procedure_code: Optional[str]
    procedure_name: Optional[str]
    procedure_icd: Optional[str]

    @validator('procedure')
    def set_procedure(cls, procedure):
        return procedure or ''


class ProcedureModel(BaseModel):
    current: List[CurrentProcedureModel]


class BlockModelFetched(TimeModel):
    id: str
    title: str
    nurse_name: Optional[str]
    sanitaire_name: Optional[str]
    assistant_name: Optional[str]
    anesthetist_name: Optional[str]
    doctor_name: Optional[str]
    doctor_id: str
    doctors_license: Optional[str]


class OperationModelFetched(TimeModel):
    parent_block_id: str
    surgery_id: str
    doc_name: str
    sur_name: Optional[str]
    type: str
    procedure: ProcedureModel
    monitoring_request: Optional[str]
    xray_type: Optional[str]
    xray_type_value: Optional[str]
    tee_request: Optional[str]
    heart_lung_machine_request: Optional[str]
    additionalEquipment: Optional[AdditionalResourceModel]
    setup_time: Optional[int]
    patient_age: Optional[Union[int, Literal['-']]]
    anesthesia: Optional[str]
    resources: Optional[dict]


class ResponseFetch(BaseModel):
    items: List[Union[BlockModelFetched, OperationModelFetched]]

    @classmethod
    @validator('items')
    def validate_root(cls, v):
        for item in v:
            if not isinstance(item, (BlockModelFetched, OperationModelFetched)):
                raise ValueError('List must only contain objects of type BlockModelFetched or OperationModelFetched')
        return v
