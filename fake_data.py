from datetime import timedelta, datetime

from faker import Faker
from models import AdditionalResourceModel, CurrentProcedureModel, ProcedureModel, BlockModelFetched, \
    OperationModelFetched, responseFetch

fake = Faker()


def get_fake_future_time(days):
    start_time = datetime.now()
    end_time = start_time + timedelta(days=days)
    return fake.date_time_between(start_date=start_time, end_date=end_time)


def generate_mock_data(numBlocks: int, maxOperations: int, rooms: int) -> responseFetch:
    blocks = []
    counter = 0
    for block_id in range(1, numBlocks):
        block_start_time = get_fake_future_time(4)
        block_end_time = block_start_time + timedelta(hours=6)
        roomId = 'room_' + str(fake.random_int(min=1, max=rooms))
        block = BlockModelFetched(
            id=block_id,
            start=block_start_time,
            end=block_end_time,
            resourceId=roomId,
            title=fake.sentence(),
            nurse_name=fake.name(),
            sanitaire_name=fake.name(),
            assistant_name=fake.name(),
            anesthetist_name=fake.name(),
            doctor_name=fake.name(),
            doctor_id=fake.random_int(1000, 9999),
            doctors_license=fake.random_number(digits=6)
        )
        for operation_id in range(1, fake.random_int(1, maxOperations)):
            op_start_time = fake.date_time_between(start_date=block_start_time, end_date=block_end_time)
            op_end_time = op_start_time + timedelta(hours=1)
            counter = counter + 1
            operation = OperationModelFetched(
                id= counter,
                start=op_start_time,
                end=op_end_time,
                resourceId=roomId,
                parent_block_id=block_id,
                surgery_id=fake.random_int(100, 999),
                doc_name=fake.name(),
                sur_name=fake.name(),
                type=fake.word(),
                procedure=ProcedureModel(
                    current=[
                        CurrentProcedureModel(
                            side=fake.word(),
                            surgery_category=fake.word(),
                            surgery_name=fake.word(),
                            procedure=fake.word(),
                            surgery_duration=fake.time(),
                            procedure_code=fake.random_number(digits=5),
                            procedure_name=fake.sentence(),
                            procedure_icd=fake.random_number(digits=5)
                        )
                    ]
                ),
                monitoring_request=fake.sentence() if fake.boolean() else None,
                xray_type=fake.word() if fake.boolean() else None,
                xray_type_value=fake.word() if fake.boolean() else None,
                tee_request=fake.sentence() if fake.boolean() else None,
                heart_lung_machine_request=fake.sentence() if fake.boolean() else None,
                additionalEquipment=AdditionalResourceModel(
                    monitor=fake.boolean(),
                    x_ray=fake.boolean(),
                    hospital_stretchers=fake.boolean(),
                    defibrillators=fake.boolean(),
                    anesthesia_machines=fake.boolean(),
                    patient_monitors=fake.boolean(),
                    sterilizers=fake.boolean(),
                    ekg_machines=fake.boolean(),
                    surgical_tables=fake.boolean(),
                    blanket_and_fluid_warmers=fake.boolean(),
                    tee=fake.boolean()
                ) if fake.boolean() else None,
                setup_time=fake.random_int(5, 60)
            )
            blocks.append(operation.dict())
        blocks.append(block.dict())
    return blocks
