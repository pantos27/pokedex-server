from typing import ClassVar
import uuid
import datetime

from pydantic import BaseModel, Field


generate_uuid = lambda: str(uuid.uuid4())
get_now = lambda : datetime.datetime.now(datetime.UTC)


class Message(BaseModel):
    type_id: ClassVar[str]

    @classmethod
    def get_message_type_from_type(cls) -> str:
        return cls.type_id.split('.')[-1]

    messageType: str = "some message type"
    messageId: str = Field(default_factory=generate_uuid)
    timestamp: str = Field(default_factory=lambda: get_now().isoformat())
    correlationId: str = Field(default_factory=generate_uuid)
