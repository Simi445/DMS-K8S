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
-- Name: auth; Type: TABLE; Schema: public; Owner: simion
--

CREATE TABLE auth (
    auth_id integer NOT NULL,
    password character varying(255) NOT NULL
);


ALTER TABLE auth OWNER TO simion;

--
-- Name: auth_auth_id_seq; Type: SEQUENCE; Schema: public; Owner: simion
--

CREATE SEQUENCE auth_auth_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE auth_auth_id_seq OWNER TO simion;

--
-- Name: auth_auth_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: simion
--

ALTER SEQUENCE auth_auth_id_seq OWNED BY auth.auth_id;


--
-- Name: auth auth_id; Type: DEFAULT; Schema: public; Owner: simion
--

ALTER TABLE ONLY auth ALTER COLUMN auth_id SET DEFAULT nextval('auth_auth_id_seq'::regclass);


--
-- Data for Name: auth; Type: TABLE DATA; Schema: public; Owner: simion
--

COPY auth (auth_id, password) FROM stdin;
1	scrypt:32768:8:1$LrHJVpq6v7clw8XP$1fb5280c8701d37b8a2a0918d18063c8a9b4c87002d0634b8c98f7e05d7dda43cd765ece41fcedd3825c42afc833996969a5217e864d24747de7d2cf3704b785
2	scrypt:32768:8:1$JRrJpM1mxZmxr18a$af0bc18d163adaded63ba90b1e26c32b95fdf06b3c9280cf7c99c7c17dab53b357bb90d82d252fc09e2c9038fa350c251d48007a99fc5500f45d61112a4accdc
\.


--
-- Name: auth_auth_id_seq; Type: SEQUENCE SET; Schema: public; Owner: simion
--

SELECT pg_catalog.setval('auth_auth_id_seq', 2, true);


--
-- Name: auth auth_pkey; Type: CONSTRAINT; Schema: public; Owner: simion
--

ALTER TABLE ONLY auth
    ADD CONSTRAINT auth_pkey PRIMARY KEY (auth_id);


--
-- PostgreSQL database dump complete
--

