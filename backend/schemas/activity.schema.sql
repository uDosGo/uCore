-- Activity Pod Schema - uCore Feed System (Pod/Nugget/Seed/Slate/Spool)
-- Stored at: ~/.ucore/pods/activity.db

CREATE TABLE IF NOT EXISTS user_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    type TEXT NOT NULL,
    title TEXT, content TEXT, url TEXT,
    contact_id INTEGER, context_id INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    importance REAL DEFAULT 0.5,
    processed BOOLEAN DEFAULT 0,
    metadata JSON,
    FOREIGN KEY (contact_id) REFERENCES contacts(id),
    FOREIGN KEY (context_id) REFERENCES contexts(id)
);
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, email TEXT, phone TEXT,
    im_handle TEXT, organization TEXT, notes TEXT,
    last_contact DATETIME, metadata JSON
);
CREATE TABLE IF NOT EXISTS contexts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, description TEXT,
    source TEXT, source_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS binder_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    context_id INTEGER, name TEXT, description TEXT,
    confidence REAL DEFAULT 0.5,
    suggested_skills TEXT, suggested_tasks TEXT,
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (context_id) REFERENCES contexts(id)
);
CREATE TABLE IF NOT EXISTS task_activity_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT, activity_id INTEGER,
    link_type TEXT DEFAULT 'source',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (activity_id) REFERENCES user_activity(id)
);
CREATE INDEX IF NOT EXISTS idx_activity_ts ON user_activity(timestamp);
CREATE INDEX IF NOT EXISTS idx_activity_contact ON user_activity(contact_id);
CREATE INDEX IF NOT EXISTS idx_activity_source ON user_activity(source);
CREATE INDEX IF NOT EXISTS idx_context_source ON contexts(source, source_id);
