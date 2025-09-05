
from ..models import conversation
class Handler:
    def __init__(self, next_handler=None):
        self.next = next_handler
    def handle(self, convo: conversation.Conversation):
        if self.next:
            return self.next.handle(convo)
        return convo