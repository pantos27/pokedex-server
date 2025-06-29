from typing import Type

from utils.rabbitmq_service import MessageSubType, MessageHandler


class MessageRouter:
    def __init__(self):
        self.handlers: list[tuple[Type[MessageSubType],MessageHandler]] = []

    def message_handler(self, message_class: Type[MessageSubType]):
        def decorator(handler: MessageHandler):
            self.handlers.append((message_class, handler))
            return handler

        return decorator
