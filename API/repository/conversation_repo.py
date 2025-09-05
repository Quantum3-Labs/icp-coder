import sqlite3

from ..models import conversation
from .. import list_api_keys

def init_schema():
    conn = sqlite3.connect('conversations.db')
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    history TEXT  NOT NULL,
    new_message TEXT NOT NULL,
    user_id INTEGER NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

def save_conversation(convo: conversation.Conversation):
    conn = sqlite3.connect('conversations.db')
    cur = conn.cursor()
    if convo.id is None:
        cur.execute('''
                    INSERT INTO conversations (history, new_message, user_id) VALUES (?, ?, ?)
                    ''',
                    (convo.serialize_history(), convo.new_message,list_api_keys.user_id))
        convo.id = cur.lastrowid
    else:
        cur.execute('''
                    UPDATE conversations SET history = ?, new_message = ?, user_id = ? WHERE id = ?
                    ''',
                    (convo.serialize_history(), convo.new_message, list_api_keys.user_id, convo.id))
    conn.commit()
    conn.close()

def load_conversation(convo_id: int) -> conversation.Conversation:
    conn = sqlite3.connect('conversations.db')
    cur = conn.cursor()
    cur.execute('''
                SELECT id, history, new_message, user_id FROM conversations WHERE id = ?
                ''', (convo_id,))
    row = cur.fetchone()
    conn.close()

    if row:
        convo_id, history_json, new_message, user_id = row
        history = conversation.Conversation.deserialize_history(history_json)
        return conversation.Conversation(history=history, new_message=new_message, convo_id=convo_id, user_id=user_id)
    return None