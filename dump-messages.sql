-- Customer Support Message Service Database Schema
-- Run this on your PostgreSQL instance to create the messages database

CREATE DATABASE messages;
\c messages;

-- Chat sessions table
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL,
    admin_id UUID NULL,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'closed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_id UUID NOT NULL,
    receiver_id UUID NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE,
    chat_session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message_type VARCHAR(20) DEFAULT 'user' -- 'user', 'admin', 'auto', 'ai', 'notification'
);

-- Indexes for performance
CREATE INDEX idx_chat_sessions_client_id ON chat_sessions(client_id);
CREATE INDEX idx_chat_sessions_admin_id ON chat_sessions(admin_id);
CREATE INDEX idx_chat_sessions_status ON chat_sessions(status);
CREATE INDEX idx_messages_chat_session ON messages(chat_session_id);
CREATE INDEX idx_messages_sender ON messages(sender_id);
CREATE INDEX idx_messages_receiver ON messages(receiver_id);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);
CREATE INDEX idx_messages_type ON messages(message_type);

-- Sample data for testing
INSERT INTO chat_sessions (id, client_id, admin_id, status) VALUES
('550e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440010', '550e8400-e29b-41d4-a716-446655440020', 'active');