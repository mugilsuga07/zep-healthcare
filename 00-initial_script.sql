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

CREATE EXTENSION vector;

CREATE TABLE IF NOT EXISTS kb (
    id uuid NOT NULL,
    name character varying(1024),
    data_type character varying(24),
    metadata JSONB,
    status character varying(24),
    created_by uuid,
    created_date timestamp with time zone,
    last_modified_by uuid,
    last_modified_date timestamp with time zone,
    is_deleted boolean DEFAULT false,
    organization_id uuid NULL,
    object_acl jsonb NULL,
    tenant_id uuid DEFAULT null
  );
  ALTER TABLE
    public.kb
  ADD
    CONSTRAINT kb_pkey PRIMARY KEY (id);

  create table IF NOT EXISTS kb_docs (
    id uuid NOT NULL,
    kb_id uuid NOT NULL,
    title text not null,
    text text null,
    url text null,
    tokens integer null,
    embedding vector(1536),
    created_by uuid,
    created_date timestamp with time zone,
    last_modified_by uuid,
    last_modified_date timestamp with time zone,
    is_deleted boolean DEFAULT false,
    organization_id uuid NULL,
    object_acl jsonb NULL,
    tenant_id uuid DEFAULT null
  );
  ALTER TABLE
    public.kb_docs
  ADD
    CONSTRAINT kb_docs_pkey PRIMARY KEY (id);
  ALTER TABLE ONLY public.kb_docs
      ADD CONSTRAINT "FK_kb_docs" FOREIGN KEY (kb_id) REFERENCES public.kb(id);

ALTER TABLE public.kb_docs ADD item_metadata jsonb NULL;
