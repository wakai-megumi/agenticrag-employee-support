import json
import sqlite3
from datetime import datetime, timezone
from app.core.config import get_settings


settings = get_settings()

def initialize_audit_db():
    """
    Initializes the audit database and creates the necessary table if it doesn't exist.
    """
    conn = sqlite3.connect(settings.audit_db_path)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            question TEXT NOT NULL,
            source_used TEXT NOT NULL,
            trace_json TEXT NOT NULL)
    ''')
    conn.commit()
    conn.close()


def write_audit_log(question: str, source_used: str, trace_json: list[str]):
    """
    Writes an audit log entry to the database.
    """
    conn = sqlite3.connect(settings.audit_db_path)
    cursor = conn.cursor()
    timestamp = datetime.now(timezone.utc).isoformat()
    cursor.execute('''
        INSERT INTO audit_log (timestamp, question, source_used, trace_json)
        VALUES (?, ?, ?, ?)
    ''', (timestamp, question, source_used, json.dumps(trace_json)))
    conn.commit()
    conn.close()