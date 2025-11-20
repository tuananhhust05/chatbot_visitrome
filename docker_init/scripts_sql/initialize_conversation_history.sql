
-- Ensure that the database corresponds to the settings given in the .env file
CREATE TABLE whatsapp_db.conversation_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    conversation_id INTEGER,
    role VARCHAR(255),
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
