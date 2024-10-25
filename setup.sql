SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

CREATE DATABASE jhm_vectordb;
\c jhm_vectordb;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS flows (  
    id uuid PRIMARY KEY,  
    name VARCHAR(255) NOT NULL,  
    description TEXT,
    status character varying(24),
    ref_entity_id uuid,
    ref_entity_type character varying(255),
    flow_type character varying(255),
    is_published boolean DEFAULT false,
    state_schema JSON,
    settings JSONB,
    parent_id uuid null,
    version_id character varying(255),
    created_by uuid,
    last_modified_by uuid,
    created_date TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    last_modified_date TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    is_deleted boolean DEFAULT false,
    tenant_id uuid DEFAULT null
);

CREATE TABLE IF NOT EXISTS flow_nodes (  
    id uuid PRIMARY KEY,  
    workflow_id uuid REFERENCES flows(id),  
    order_num INT NULL,
    is_trigger boolean NOT NULL default false,
    name character varying(255) NOT NULL,
    description TEXT,
    type character varying(120),
    sub_type character varying(120),
    parent_id uuid,
    settings JSONB,
    ref_entity_id uuid,
    ref_entity_type character varying(255),    
    created_by uuid,
    last_modified_by uuid,
    created_date TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    last_modified_date TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    is_deleted boolean DEFAULT false,
    tenant_id uuid DEFAULT null
);

CREATE TABLE IF NOT EXISTS flow_node_embeddings (
    id UUID PRIMARY KEY,
    phrase VARCHAR(255),
    embedding vector(1536),
    node_id UUID REFERENCES flow_nodes(id),
    workflow_id uuid REFERENCES flows(id), 
    created_by uuid,
    last_modified_by uuid,
    created_date TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    last_modified_date TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    is_deleted boolean DEFAULT false,
    tenant_id uuid DEFAULT null
);

CREATE TABLE IF NOT EXISTS flow_instances (  
    id uuid PRIMARY KEY,  
    workflow_id uuid REFERENCES flows(id), 
    node_id uuid, 
    status VARCHAR(50) NOT NULL,  
    start_time TIMESTAMP DEFAULT NOW(),  
    end_time TIMESTAMP,  
    result JSONB,
    message_history JSONB,
    state_schema JSON,
    ref_entity_id uuid,
    ref_entity_type character varying(255),
    created_by uuid,
    last_modified_by uuid,
    created_date TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    last_modified_date TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    is_deleted boolean DEFAULT false,
    tenant_id uuid DEFAULT null
);

CREATE TABLE IF NOT EXISTS flow_instance_nodes (  
    id uuid PRIMARY KEY,  
    instance_id uuid REFERENCES flow_instances(id),  
    node_id uuid,  
    workflow_id uuid REFERENCES flows(id),  
    status VARCHAR(50) NOT NULL,  
    is_simulation boolean NOT NULL DEFAULT false,  
    input JSONB,  
    output JSONB,
    created_by uuid,
    last_modified_by uuid,
    created_date TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    last_modified_date TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    is_deleted boolean DEFAULT false,
    tenant_id uuid DEFAULT null
);

CREATE TABLE IF NOT EXISTS flow_instance_logs (  
    id uuid PRIMARY KEY,  
    instance_id uuid REFERENCES flow_instances(id),  
    timestamp TIMESTAMP DEFAULT NOW(),  
    message TEXT,
    created_by uuid,
    last_modified_by uuid,
    created_date TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    last_modified_date TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    is_deleted boolean DEFAULT false,
    tenant_id uuid DEFAULT null
);

CREATE TABLE IF NOT EXISTS flow_intents (  
    id uuid PRIMARY KEY,
    name varchar(100),  
    phrases TEXT[],  
    description TEXT,
    confident_score decimal,
    created_by uuid,
    last_modified_by uuid,
    created_date TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    last_modified_date TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    is_deleted boolean DEFAULT false,
    tenant_id uuid DEFAULT null
);

CREATE TABLE IF NOT EXISTS flow_entities (  
    id uuid PRIMARY KEY,  
    value TEXT[],  
    name varchar(120),
    created_by uuid,
    last_modified_by uuid,
    created_date TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    last_modified_date TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    is_deleted boolean DEFAULT false,
    tenant_id uuid DEFAULT null
);

CREATE TABLE IF NOT EXISTS flow_intent_entities (  
    id uuid PRIMARY KEY,  
    intent_id uuid REFERENCES flow_intents(id),  
    entity_id uuid REFERENCES flow_entities(id),  
    created_by uuid,
    last_modified_by uuid,
    created_date TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    last_modified_date TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'UTC'),
    is_deleted boolean DEFAULT false,
    tenant_id uuid DEFAULT null
);