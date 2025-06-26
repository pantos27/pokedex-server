
class MessageRouter:
    def __init__(self):
        self.handlers = []
    def message_handler(self, message_class, has_response=False):
        def decorator(func):
            self.handlers.append((message_class, func, has_response))
            return func
        return decorator
