import json
class Conversation:
    def __init__(self, history=None, new_message="", convo_id=None, user_id=None):
        self.history = history if history else []
        self.new_message = new_message
        self.id =convo_id
        self.user_id = user_id if user_id else None

    def add_turn(self, role, content):
        self.history.append((role, content))

    def set_new_message(self, message):
        self.new_message = message

    def set_user_id(self, user_id):
        self.user_id = user_id
    def __repr__(self):
        return f"Conversation(history={self.history}, new_message='{self.new_message}')"
    def build_conversation_history(self):
        contents = []
        for role, text in self.history:
            contents.append({
                "role": role,
                "parts": [{"text": text}]
            })
        if self.new_message:
            contents.append({
                "role": "user",
                "parts": [{"text": self.new_message}]
            })
        return contents

    def serialize_history(self):
        return json.dumps(self.history)

    @staticmethod
    def deserialize_history(history_json):
        return json.loads(history_json)