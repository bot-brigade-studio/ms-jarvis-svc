--
-- PostgreSQL database dump
--

-- Dumped from database version 14.13 (Homebrew)
-- Dumped by pg_dump version 14.13 (Homebrew)

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

--
-- Name: statusenum; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.statusenum AS ENUM (
    'ACTIVE',
    'INACTIVE',
    'SUSPENDED',
    'BANNED',
    'DELETED',
    'PENDING'
);


ALTER TYPE public.statusenum OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: bot_configs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bot_configs (
    is_current boolean,
    version integer,
    name character varying(255),
    model_name character varying(255) NOT NULL,
    custom_instructions text,
    max_context_tokens integer,
    max_output_tokens integer,
    temperature double precision,
    top_p double precision,
    top_k integer,
    bot_id uuid,
    tenant_id uuid,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    deleted_by uuid
);


ALTER TABLE public.bot_configs OWNER TO postgres;

--
-- Name: bots; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bots (
    name character varying(255) NOT NULL,
    avatar_url character varying(255),
    tagline character varying(255),
    description text,
    greeting text,
    is_bot_definition_public boolean,
    status public.statusenum,
    tenant_id uuid,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    deleted_by uuid
);


ALTER TABLE public.bots OWNER TO postgres;

--
-- Name: config_variables; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.config_variables (
    key character varying(255),
    value jsonb,
    config_id uuid,
    tenant_id uuid,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    deleted_by uuid
);


ALTER TABLE public.config_variables OWNER TO postgres;

--
-- Name: mst_categories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.mst_categories (
    name character varying(255) NOT NULL,
    slug character varying(255) NOT NULL,
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    deleted_by uuid
);


ALTER TABLE public.mst_categories OWNER TO postgres;

--
-- Name: mst_items; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.mst_items (
    category_id uuid,
    name character varying(255) NOT NULL,
    description character varying(255),
    id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    created_by uuid,
    updated_by uuid,
    deleted_at timestamp with time zone,
    deleted_by uuid
);


ALTER TABLE public.mst_items OWNER TO postgres;

--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alembic_version (version_num) FROM stdin;
20241127012047
\.


--
-- Data for Name: bot_configs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.bot_configs (is_current, version, name, model_name, custom_instructions, max_context_tokens, max_output_tokens, temperature, top_p, top_k, bot_id, tenant_id, id, created_at, updated_at, created_by, updated_by, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: bots; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.bots (name, avatar_url, tagline, description, greeting, is_bot_definition_public, status, tenant_id, id, created_at, updated_at, created_by, updated_by, deleted_at, deleted_by) FROM stdin;
string	string	string	string	string	t	ACTIVE	\N	067450b5-0efd-7ef8-8000-b71a4fe86642	2024-11-26 06:42:08.93305+07	\N	\N	\N	\N	\N
WOKE GA SIH	string	string	string	string	t	ACTIVE	067423b0-81b8-7dcf-8000-b593277c0754	067450c1-3215-7097-8000-f06f916be15a	2024-11-26 06:45:23.127693+07	\N	067423b0-81fa-702b-8000-b03b6db1eb93	067423b0-81fa-702b-8000-b03b6db1eb93	\N	\N
YOI MAMEN	string	string	string	string	t	ACTIVE	067423b0-81b8-7dcf-8000-b593277c0754	067450c3-30f0-79c7-8000-25bbc354c2f1	2024-11-26 06:45:55.057656+07	\N	067423b0-81fa-702b-8000-b03b6db1eb93	067423b0-81fa-702b-8000-b03b6db1eb93	\N	\N
HARUS BISA	string	string	string	string	t	ACTIVE	067423b0-81b8-7dcf-8000-b593277c0754	0674511b-7a76-7598-8000-9e1e29108ff5	2024-11-26 07:09:27.650294+07	\N	067423b0-81fa-702b-8000-b03b6db1eb93	067423b0-81fa-702b-8000-b03b6db1eb93	\N	\N
\.


--
-- Data for Name: config_variables; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.config_variables (key, value, config_id, tenant_id, id, created_at, updated_at, created_by, updated_by, deleted_at, deleted_by) FROM stdin;
\.


--
-- Data for Name: mst_categories; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.mst_categories (name, slug, id, created_at, updated_at, created_by, updated_by, deleted_at, deleted_by) FROM stdin;
bot category	bot-category	0674617f-ee38-7e5c-8000-19d5e345aee6	2024-11-27 01:48:30.889247+07	\N	\N	\N	\N	\N
\.


--
-- Data for Name: mst_items; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.mst_items (category_id, name, description, id, created_at, updated_at, created_by, updated_by, deleted_at, deleted_by) FROM stdin;
0674617f-ee38-7e5c-8000-19d5e345aee6	Finance		06746181-e3a7-78e1-8000-3f286b348fb7	2024-11-27 01:49:02.225427+07	\N	\N	\N	\N	\N
0674617f-ee38-7e5c-8000-19d5e345aee6	Academics		06746182-44fb-77e9-8000-65d07631d609	2024-11-27 01:49:08.309956+07	\N	\N	\N	\N	\N
\.


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: bot_configs bot_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bot_configs
    ADD CONSTRAINT bot_configs_pkey PRIMARY KEY (id);


--
-- Name: bots bots_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bots
    ADD CONSTRAINT bots_pkey PRIMARY KEY (id);


--
-- Name: config_variables config_variables_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.config_variables
    ADD CONSTRAINT config_variables_pkey PRIMARY KEY (id);


--
-- Name: mst_categories mst_categories_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mst_categories
    ADD CONSTRAINT mst_categories_name_key UNIQUE (name);


--
-- Name: mst_categories mst_categories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mst_categories
    ADD CONSTRAINT mst_categories_pkey PRIMARY KEY (id);


--
-- Name: mst_categories mst_categories_slug_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mst_categories
    ADD CONSTRAINT mst_categories_slug_key UNIQUE (slug);


--
-- Name: mst_items mst_items_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mst_items
    ADD CONSTRAINT mst_items_pkey PRIMARY KEY (id);


--
-- Name: idx_category_id_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_category_id_name ON public.mst_items USING btree (category_id, name);


--
-- Name: ix_bot_configs_created_by; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_bot_configs_created_by ON public.bot_configs USING btree (created_by);


--
-- Name: ix_bot_configs_deleted_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_bot_configs_deleted_at ON public.bot_configs USING btree (deleted_at);


--
-- Name: ix_bot_configs_tenant_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_bot_configs_tenant_id ON public.bot_configs USING btree (tenant_id);


--
-- Name: ix_bots_created_by; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_bots_created_by ON public.bots USING btree (created_by);


--
-- Name: ix_bots_deleted_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_bots_deleted_at ON public.bots USING btree (deleted_at);


--
-- Name: ix_bots_tenant_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_bots_tenant_id ON public.bots USING btree (tenant_id);


--
-- Name: ix_config_variables_created_by; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_config_variables_created_by ON public.config_variables USING btree (created_by);


--
-- Name: ix_config_variables_deleted_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_config_variables_deleted_at ON public.config_variables USING btree (deleted_at);


--
-- Name: ix_config_variables_tenant_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_config_variables_tenant_id ON public.config_variables USING btree (tenant_id);


--
-- Name: ix_mst_categories_created_by; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_mst_categories_created_by ON public.mst_categories USING btree (created_by);


--
-- Name: ix_mst_categories_deleted_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_mst_categories_deleted_at ON public.mst_categories USING btree (deleted_at);


--
-- Name: ix_mst_items_created_by; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_mst_items_created_by ON public.mst_items USING btree (created_by);


--
-- Name: ix_mst_items_deleted_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_mst_items_deleted_at ON public.mst_items USING btree (deleted_at);


--
-- Name: bot_configs bot_configs_bot_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bot_configs
    ADD CONSTRAINT bot_configs_bot_id_fkey FOREIGN KEY (bot_id) REFERENCES public.bots(id);


--
-- Name: config_variables config_variables_config_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.config_variables
    ADD CONSTRAINT config_variables_config_id_fkey FOREIGN KEY (config_id) REFERENCES public.bot_configs(id);


--
-- Name: mst_items mst_items_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.mst_items
    ADD CONSTRAINT mst_items_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.mst_categories(id);


--
-- PostgreSQL database dump complete
--

