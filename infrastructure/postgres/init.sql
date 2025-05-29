-- Erstelle Schema für heydok-video
CREATE SCHEMA IF NOT EXISTS heydok;

-- Setze Suchpfad
SET search_path TO heydok, public;

-- Aktiviere UUID Extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enum Types
CREATE TYPE user_role AS ENUM ('physician', 'patient', 'admin', 'observer');
CREATE TYPE room_status AS ENUM ('scheduled', 'active', 'ended', 'cancelled');
CREATE TYPE participant_status AS ENUM ('invited', 'joined', 'left', 'disconnected');
CREATE TYPE recording_status AS ENUM ('pending', 'recording', 'processing', 'completed', 'failed');
CREATE TYPE audit_action AS ENUM ('create', 'read', 'update', 'delete', 'join', 'leave', 'start_recording', 'stop_recording');

-- Users Tabelle
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL, -- ID aus heydok System
    email VARCHAR(255) UNIQUE NOT NULL,
    role user_role NOT NULL,
    encrypted_name TEXT NOT NULL, -- Verschlüsselter Name für GDPR
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Rooms Tabelle
CREATE TABLE rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id VARCHAR(255) UNIQUE NOT NULL, -- LiveKit Room ID
    name VARCHAR(255) NOT NULL,
    status room_status NOT NULL DEFAULT 'scheduled',
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    scheduled_start TIMESTAMP WITH TIME ZONE,
    scheduled_end TIMESTAMP WITH TIME ZONE,
    actual_start TIMESTAMP WITH TIME ZONE,
    actual_end TIMESTAMP WITH TIME ZONE,
    max_participants INTEGER DEFAULT 20,
    enable_recording BOOLEAN DEFAULT false,
    enable_chat BOOLEAN DEFAULT true,
    enable_screen_share BOOLEAN DEFAULT true,
    waiting_room_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Participants Tabelle
CREATE TABLE participants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    participant_id VARCHAR(255) NOT NULL, -- LiveKit Participant ID
    status participant_status NOT NULL DEFAULT 'invited',
    role user_role NOT NULL,
    join_token TEXT, -- Verschlüsselter JWT Token
    joined_at TIMESTAMP WITH TIME ZONE,
    left_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    is_presenter BOOLEAN DEFAULT false,
    can_publish BOOLEAN DEFAULT true,
    can_subscribe BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(room_id, user_id)
);

-- Recordings Tabelle
CREATE TABLE recordings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
    recording_id VARCHAR(255) UNIQUE NOT NULL, -- LiveKit Recording ID
    status recording_status NOT NULL DEFAULT 'pending',
    started_by UUID REFERENCES users(id) ON DELETE SET NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    file_size_bytes BIGINT,
    encrypted_file_path TEXT, -- Verschlüsselter Dateipfad
    encryption_key_id VARCHAR(255), -- Key ID für Entschlüsselung
    consent_given BOOLEAN DEFAULT false,
    consent_given_by UUID[] DEFAULT ARRAY[]::UUID[], -- Array von User IDs die zugestimmt haben
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE, -- Soft delete für GDPR
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Chat Messages Tabelle
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES users(id) ON DELETE SET NULL,
    encrypted_message TEXT NOT NULL, -- Verschlüsselte Nachricht
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE, -- Soft delete
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Audit Log Tabelle (HIPAA Compliance)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action audit_action NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(255),
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Meeting Links Tabelle
CREATE TABLE meeting_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    room_id UUID REFERENCES rooms(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    max_uses INTEGER DEFAULT 1,
    use_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(room_id, user_id)
);

-- Indexes für Performance
CREATE INDEX idx_users_external_id ON users(external_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_rooms_status ON rooms(status);
CREATE INDEX idx_rooms_scheduled_start ON rooms(scheduled_start);
CREATE INDEX idx_participants_room_id ON participants(room_id);
CREATE INDEX idx_participants_user_id ON participants(user_id);
CREATE INDEX idx_recordings_room_id ON recordings(room_id);
CREATE INDEX idx_recordings_status ON recordings(status);
CREATE INDEX idx_chat_messages_room_id ON chat_messages(room_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_meeting_links_token ON meeting_links(token);
CREATE INDEX idx_meeting_links_expires_at ON meeting_links(expires_at);

-- Trigger für updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_rooms_updated_at BEFORE UPDATE ON rooms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_participants_updated_at BEFORE UPDATE ON participants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_recordings_updated_at BEFORE UPDATE ON recordings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Funktion für Audit Logging
CREATE OR REPLACE FUNCTION create_audit_log(
    p_user_id UUID,
    p_action audit_action,
    p_resource_type VARCHAR(50),
    p_resource_id UUID,
    p_ip_address INET,
    p_user_agent TEXT,
    p_request_id VARCHAR(255),
    p_success BOOLEAN,
    p_error_message TEXT,
    p_metadata JSONB
)
RETURNS UUID AS $$
DECLARE
    v_audit_id UUID;
BEGIN
    INSERT INTO audit_logs (
        user_id, action, resource_type, resource_id,
        ip_address, user_agent, request_id, success,
        error_message, metadata
    ) VALUES (
        p_user_id, p_action, p_resource_type, p_resource_id,
        p_ip_address, p_user_agent, p_request_id, p_success,
        p_error_message, p_metadata
    ) RETURNING id INTO v_audit_id;
    
    RETURN v_audit_id;
END;
$$ LANGUAGE plpgsql;

-- Partitionierung für Audit Logs (für bessere Performance bei großen Datenmengen)
-- Erstelle Partitionen für jeden Monat automatisch
CREATE OR REPLACE FUNCTION create_monthly_audit_partition()
RETURNS void AS $$
DECLARE
    start_date date;
    end_date date;
    partition_name text;
BEGIN
    start_date := date_trunc('month', CURRENT_DATE);
    end_date := start_date + interval '1 month';
    partition_name := 'audit_logs_' || to_char(start_date, 'YYYY_MM');
    
    -- Prüfe ob Partition bereits existiert
    IF NOT EXISTS (
        SELECT 1 FROM pg_class
        WHERE relname = partition_name
    ) THEN
        EXECUTE format(
            'CREATE TABLE %I PARTITION OF audit_logs
            FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Erstelle initiale Partition
-- ALTER TABLE audit_logs PARTITION BY RANGE (created_at);
-- SELECT create_monthly_audit_partition();

-- Grants für Anwendungsuser (wird in Produktion angepasst)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA heydok TO heydok_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA heydok TO heydok_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA heydok TO heydok_app; 