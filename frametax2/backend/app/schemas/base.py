import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TimestampedSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
