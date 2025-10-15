--
-- PostgreSQL database dump
--

-- Dumped from database version 9.6.2
-- Dumped by pg_dump version 9.6.2

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: user; Type: TABLE; Schema: public; Owner: simion
--

CREATE TABLE "user" (
    user_id integer NOT NULL,
    username character varying(20) NOT NULL,
    email character varying(20) NOT NULL,
    role character varying(20) NOT NULL
);


ALTER TABLE "user" OWNER TO simion;

--
-- Name: user_auth; Type: TABLE; Schema: public; Owner: simion
--

CREATE TABLE user_auth (
    id integer NOT NULL,
    user_id integer NOT NULL,
    auth_id integer NOT NULL
);


ALTER TABLE user_auth OWNER TO simion;

--
-- Name: user_auth_id_seq; Type: SEQUENCE; Schema: public; Owner: simion
--

CREATE SEQUENCE user_auth_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_auth_id_seq OWNER TO simion;

--
-- Name: user_auth_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: simion
--

ALTER SEQUENCE user_auth_id_seq OWNED BY user_auth.id;


--
-- Name: user_user_id_seq; Type: SEQUENCE; Schema: public; Owner: simion
--

CREATE SEQUENCE user_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE user_user_id_seq OWNER TO simion;

--
-- Name: user_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: simion
--

ALTER SEQUENCE user_user_id_seq OWNED BY "user".user_id;


--
-- Name: user user_id; Type: DEFAULT; Schema: public; Owner: simion
--

ALTER TABLE ONLY "user" ALTER COLUMN user_id SET DEFAULT nextval('user_user_id_seq'::regclass);


--
-- Name: user_auth id; Type: DEFAULT; Schema: public; Owner: simion
--

ALTER TABLE ONLY user_auth ALTER COLUMN id SET DEFAULT nextval('user_auth_id_seq'::regclass);


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: simion
--

COPY "user" (user_id, username, email, role) FROM stdin;
1	simi	simi@gmail.com	user
2	simiadmin	simiadmin@gmaial	admin
\.


--
-- Data for Name: user_auth; Type: TABLE DATA; Schema: public; Owner: simion
--

COPY user_auth (id, user_id, auth_id) FROM stdin;
1	1	1
2	2	2
\.


--
-- Name: user_auth_id_seq; Type: SEQUENCE SET; Schema: public; Owner: simion
--

SELECT pg_catalog.setval('user_auth_id_seq', 2, true);


--
-- Name: user_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: simion
--

SELECT pg_catalog.setval('user_user_id_seq', 2, true);


--
-- Name: user_auth user_auth_pkey; Type: CONSTRAINT; Schema: public; Owner: simion
--

ALTER TABLE ONLY user_auth
    ADD CONSTRAINT user_auth_pkey PRIMARY KEY (id);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: simion
--

ALTER TABLE ONLY "user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (user_id);


--
-- Name: user_auth user_auth_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: simion
--

ALTER TABLE ONLY user_auth
    ADD CONSTRAINT user_auth_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(user_id);


--
-- PostgreSQL database dump complete
--

