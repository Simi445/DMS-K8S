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
-- Name: device; Type: TABLE; Schema: public; Owner: simion
--

CREATE TABLE device (
    device_id integer NOT NULL,
    user_id integer NOT NULL,
    name character varying(20) NOT NULL,
    status character varying(20) NOT NULL,
    consumption character varying(20) NOT NULL
);


ALTER TABLE device OWNER TO simion;

--
-- Name: device_device_id_seq; Type: SEQUENCE; Schema: public; Owner: simion
--

CREATE SEQUENCE device_device_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE device_device_id_seq OWNER TO simion;

--
-- Name: device_device_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: simion
--

ALTER SEQUENCE device_device_id_seq OWNED BY device.device_id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: simion
--

CREATE TABLE users (
    user_id integer NOT NULL
);


ALTER TABLE users OWNER TO simion;

--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: simion
--

CREATE SEQUENCE users_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE users_user_id_seq OWNER TO simion;

--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: simion
--

ALTER SEQUENCE users_user_id_seq OWNED BY users.user_id;


--
-- Name: device device_id; Type: DEFAULT; Schema: public; Owner: simion
--

ALTER TABLE ONLY device ALTER COLUMN device_id SET DEFAULT nextval('device_device_id_seq'::regclass);


--
-- Name: users user_id; Type: DEFAULT; Schema: public; Owner: simion
--

ALTER TABLE ONLY users ALTER COLUMN user_id SET DEFAULT nextval('users_user_id_seq'::regclass);


--
-- Data for Name: device; Type: TABLE DATA; Schema: public; Owner: simion
--

COPY device (device_id, user_id, name, status, consumption) FROM stdin;
1	1	Electric Castle	active	1200
\.


--
-- Name: device_device_id_seq; Type: SEQUENCE SET; Schema: public; Owner: simion
--

SELECT pg_catalog.setval('device_device_id_seq', 1, true);


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: simion
--

COPY users (user_id) FROM stdin;
1
2
\.


--
-- Name: users_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: simion
--

SELECT pg_catalog.setval('users_user_id_seq', 1, false);


--
-- Name: device device_pkey; Type: CONSTRAINT; Schema: public; Owner: simion
--

ALTER TABLE ONLY device
    ADD CONSTRAINT device_pkey PRIMARY KEY (device_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: simion
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: device device_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: simion
--

ALTER TABLE ONLY device
    ADD CONSTRAINT device_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(user_id);


--
-- PostgreSQL database dump complete
--

