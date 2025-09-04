
from API.models.conversation import Conversation
class Handler:
    def __init__(self, next_handler=None):
        self.next = next_handler
    def handle(self, convo: Conversation):
        if self.next:
            return self.next.handle(convo)
        return convo