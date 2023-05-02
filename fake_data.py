from faker import Faker
from models import BlockModelFetched, OperationModelFetched

fake = Faker()


def createMultipleNames(num):
    s = ""
    sep = ""
    for i in range(num):
        s += sep
        sep = ", "
        s += fake.name()
    return s


# Create a mock BlockModelFetched object
def createBlock():
    return BlockModelFetched(
        id=1,
        title=fake.sentence(),
        nurse_name=createMultipleNames(2),
        sanitaire_name=createMultipleNames(2),
        assistant_name=createMultipleNames(3),
        anesthetist_name=createMultipleNames(2),
        doctor_name=fake.name(),
        doctor_id=1,
        doctors_license=fake.uuid4()
    )


def createOperation(blockId):
    return OperationModelFetched(
        parent_block_id=blockId,
        surgery_id=1,
        sur_name=fake.name(),
        type=fake.word(),
        monitoring_request=fake.sentence(),
        xray_type=fake.word(),
        xray_type_value=fake.word(),
        tee_request=fake.sentence(),
        heart_lung_machine_request=fake.sentence(),
        setup_time=fake.random_int(),
        additional_equipment={
            'monitor': fake.boolean(),
            'x_ray': fake.boolean(),
            'hospital_stretchers': fake.boolean(),
            'defibrillators': fake.boolean(),
            'anesthesia_machines': fake.boolean(),
            'patient_monitors': fake.boolean(),
            'sterilizers': fake.boolean(),
            'ekg_machines': fake.boolean(),
            'surgical_tables': fake.boolean(),
            'blanket_and_fluid_warmers': fake.boolean(),
            'tee': fake.boolean()
        }
    )


def createBlocksAndCases(num_blocks, num_cases):
    blocks_and_cases = []
    for i in range(num_blocks):
        block = createBlock()
        blocks_and_cases.append(block.to_dict())
        for j in range(num_cases):
            case = createOperation(block.id)
            blocks_and_cases.append(case.to_dict())
    return blocks_and_cases
