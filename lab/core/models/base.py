import uuid
from database import Base

def generate_uuid():
    return str(uuid.uuid4())
