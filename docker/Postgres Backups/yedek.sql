--
-- PostgreSQL database dump
--

-- Dumped from database version 14.4 (Debian 14.4-1.pgdg110+1)
-- Dumped by pg_dump version 14.3 (Ubuntu 14.3-1.pgdg20.04+1)

-- Started on 2022-06-27 13:03:25 +03

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
-- TOC entry 3 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: tenis
--

--CREATE SCHEMA public;


---ALTER SCHEMA public OWNER TO tenis;

--
-- TOC entry 3390 (class 0 OID 0)
-- Dependencies: 3
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: tenis
--

COMMENT ON SCHEMA public IS 'standard public schema';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 220 (class 1259 OID 24634)
-- Name: AOSType; Type: TABLE; Schema: public; Owner: tenis
--

CREATE TABLE public."AOSType" (
    id bigint NOT NULL,
    name text NOT NULL,
    court_point_area_id bigint NOT NULL,
    save_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL
);


ALTER TABLE public."AOSType" OWNER TO tenis;

--
-- TOC entry 218 (class 1259 OID 24619)
-- Name: Court; Type: TABLE; Schema: public; Owner: tenis
--

CREATE TABLE public."Court" (
    id bigint NOT NULL,
    name text NOT NULL,
    court_type_id bigint NOT NULL,
    save_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL
);


ALTER TABLE public."Court" OWNER TO tenis;

--
-- TOC entry 216 (class 1259 OID 24609)
-- Name: CourtPointArea; Type: TABLE; Schema: public; Owner: tenis
--

CREATE TABLE public."CourtPointArea" (
    id bigint NOT NULL,
    name text NOT NULL,
    area_array bytea,
    save_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL
);


ALTER TABLE public."CourtPointArea" OWNER TO tenis;

--
-- TOC entry 215 (class 1259 OID 24608)
-- Name: CourtPointArea_id_seq; Type: SEQUENCE; Schema: public; Owner: tenis
--

ALTER TABLE public."CourtPointArea" ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public."CourtPointArea_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 214 (class 1259 OID 24599)
-- Name: CourtType; Type: TABLE; Schema: public; Owner: tenis
--

CREATE TABLE public."CourtType" (
    id bigint NOT NULL,
    name text NOT NULL,
    save_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL
);


ALTER TABLE public."CourtType" OWNER TO tenis;

--
-- TOC entry 213 (class 1259 OID 24598)
-- Name: CourtType_id_seq; Type: SEQUENCE; Schema: public; Owner: tenis
--

ALTER TABLE public."CourtType" ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public."CourtType_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 217 (class 1259 OID 24618)
-- Name: Court_id_seq; Type: SEQUENCE; Schema: public; Owner: tenis
--

ALTER TABLE public."Court" ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public."Court_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 210 (class 1259 OID 24578)
-- Name: Player; Type: TABLE; Schema: public; Owner: tenis
--

CREATE TABLE public."Player" (
    id bigint NOT NULL,
    name text NOT NULL,
    birthday timestamp without time zone,
    gender character(1) NOT NULL,
    save_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_deleted boolean DEFAULT false NOT NULL
);


ALTER TABLE public."Player" OWNER TO tenis;

--
-- TOC entry 209 (class 1259 OID 24577)
-- Name: Player_id_seq; Type: SEQUENCE; Schema: public; Owner: tenis
--

ALTER TABLE public."Player" ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public."Player_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 222 (class 1259 OID 24649)
-- Name: PlayingData; Type: TABLE; Schema: public; Owner: tenis
--

CREATE TABLE public."PlayingData" (
    id bigint NOT NULL,
    player_id bigint NOT NULL,
    court_id bigint NOT NULL,
    aos_type_id bigint NOT NULL,
    stream_id bigint NOT NULL,
    score double precision,
    ball_position_area bytea,
    player_position_area bytea,
    save_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    is_deleted boolean DEFAULT false NOT NULL
);


ALTER TABLE public."PlayingData" OWNER TO tenis;

--
-- TOC entry 221 (class 1259 OID 24648)
-- Name: PlayingData_id_seq; Type: SEQUENCE; Schema: public; Owner: tenis
--

ALTER TABLE public."PlayingData" ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public."PlayingData_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 212 (class 1259 OID 24588)
-- Name: Stream; Type: TABLE; Schema: public; Owner: tenis
--

CREATE TABLE public."Stream" (
    id bigint NOT NULL,
    name text NOT NULL,
    source text NOT NULL,
    court_line_array bytea,
    kafka_topic_name text,
    save_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_activated boolean DEFAULT true NOT NULL,
    is_deleted boolean DEFAULT true NOT NULL
);


ALTER TABLE public."Stream" OWNER TO tenis;

--
-- TOC entry 211 (class 1259 OID 24587)
-- Name: Stream_id_seq; Type: SEQUENCE; Schema: public; Owner: tenis
--

ALTER TABLE public."Stream" ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public."Stream_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 219 (class 1259 OID 24633)
-- Name: aostype_id_seq; Type: SEQUENCE; Schema: public; Owner: tenis
--

ALTER TABLE public."AOSType" ALTER COLUMN id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.aostype_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 3382 (class 0 OID 24634)
-- Dependencies: 220
-- Data for Name: AOSType; Type: TABLE DATA; Schema: public; Owner: tenis
--

COPY public."AOSType" (id, name, court_point_area_id, save_date, is_deleted) FROM stdin;
3	Yer Vuruşu Derinliği	1	2022-06-27 13:00:18.115275	f
\.


--
-- TOC entry 3380 (class 0 OID 24619)
-- Dependencies: 218
-- Data for Name: Court; Type: TABLE DATA; Schema: public; Owner: tenis
--

COPY public."Court" (id, name, court_type_id, save_date, is_deleted) FROM stdin;
1	inönü	3	2022-06-26 21:51:40.947073	f
\.


--
-- TOC entry 3378 (class 0 OID 24609)
-- Dependencies: 216
-- Data for Name: CourtPointArea; Type: TABLE DATA; Schema: public; Owner: tenis
--

COPY public."CourtPointArea" (id, name, area_array, save_date, is_deleted) FROM stdin;
1	derinlik	\\x10	2022-06-27 12:58:57.993893	f
2	hassasiyet	\\x10	2022-06-27 13:02:14.174981	f
3	servis	\\x10	2022-06-27 13:02:31.122927	f
\.


--
-- TOC entry 3376 (class 0 OID 24599)
-- Dependencies: 214
-- Data for Name: CourtType; Type: TABLE DATA; Schema: public; Owner: tenis
--

COPY public."CourtType" (id, name, save_date, is_deleted) FROM stdin;
1	grass	2022-06-26 21:50:31.818374	f
2	clay	2022-06-26 21:50:47.324141	f
3	hard	2022-06-26 21:50:57.875415	f
\.


--
-- TOC entry 3372 (class 0 OID 24578)
-- Dependencies: 210
-- Data for Name: Player; Type: TABLE DATA; Schema: public; Owner: tenis
--

COPY public."Player" (id, name, birthday, gender, save_date, is_deleted) FROM stdin;
1	Oyuncu-1	1998-04-08 19:15:00.393	E	2022-06-26 21:47:23.524802	f
\.


--
-- TOC entry 3384 (class 0 OID 24649)
-- Dependencies: 222
-- Data for Name: PlayingData; Type: TABLE DATA; Schema: public; Owner: tenis
--

COPY public."PlayingData" (id, player_id, court_id, aos_type_id, stream_id, score, ball_position_area, player_position_area, save_date, is_deleted) FROM stdin;
\.


--
-- TOC entry 3374 (class 0 OID 24588)
-- Dependencies: 212
-- Data for Name: Stream; Type: TABLE DATA; Schema: public; Owner: tenis
--

COPY public."Stream" (id, name, source, court_line_array, kafka_topic_name, save_date, is_activated, is_deleted) FROM stdin;
1	tenis_saha_1	video_1.mp4	\\x8004953a020000000000005d94288c156e756d70792e636f72652e6d756c74696172726179948c0c5f7265636f6e7374727563749493948c056e756d7079948c076e6461727261799493944b0085944301629487945294284b014b04859468048c0564747970659493948c02663494898887945294284b038c013c944e4e4e4affffffff4affffffff4b00749462894310c0d019442fe484439d73a244ad7f844394749462680368064b008594680887945294284b014b0485946810894310c3f6b443040f5d444b40c5445c6a5b4494749462680368064b008594680887945294284b014b04859468108943107c0903445d1bf4433dffae44e2eef24394749462680368064b008594680887945294284b014b0485946810894310c0d019442fe48443c3f6b443040f5d4494749462680368064b008594680887945294284b014b04859468108943109d73a244ad7f84434b40c5445c6a5b4494749462680368064b008594680887945294284b014b04859468108943105a592f4488d78443bade0044e7d95c4494749462680368064b008594680887945294284b014b048594681089431009c69744398c84436356b244b39e5b4494749462680368064b008594680887945294284b014b0485946810894310d0fd6f441f40b1431cc571441ba0264494749462680368064b008594680887945294284b014b0485946810894310d9a028449080b143ab9f9b44c7ffb04394749462680368064b008594680887945294284b014b0485946810894310871311442e0127448117a944503f264494749462652e	tenis_saha_1-0-294767743888597775794085898248448255248	2022-06-23 11:06:52.393404	t	t
2	tenis_saha_2	video_2.mp4	\\x8004953a020000000000005d94288c156e756d70792e636f72652e6d756c74696172726179948c0c5f7265636f6e7374727563749493948c056e756d7079948c076e6461727261799493944b0085944301629487945294284b014b04859468048c0564747970659493948c02663494898887945294284b038c013c944e4e4e4affffffff4affffffff4b007494628943105259064410808a43ee4cae44460b8b4394749462680368064b008594680887945294284b014b048594681089431094659243aebf5f44c3e2ca4439765f4494749462680368064b008594680887945294284b014b048594681089431051cddc4356c101449b81b94446de014494749462680368064b008594680887945294284b014b04859468108943105259064410808a4394659243aebf5f4494749462680368064b008594680887945294284b014b0485946810894310ee4cae44460b8b43c3e2ca4439765f4494749462680368064b008594680887945294284b014b0485946810894310094621448f918a43a71ae6436fb65f4494749462680368064b008594680887945294284b014b048594681089431062e8a044dff98a436720b644657f5f4494749462680368064b008594680887945294284b014b0485946810894310743d71441ed8bc43684b704413842e4494749462680368064b008594680887945294284b014b048594681089431018c61944c9aebc43ac5aa4447401bd4394749462680368064b008594680887945294284b014b048594681089431059c5014449892e441160af44dd7e2e4494749462652e	tenis_saha_2-0-107250555593954457252490986489618039834	2022-06-25 11:28:19.54419	t	t
\.


--
-- TOC entry 3391 (class 0 OID 0)
-- Dependencies: 215
-- Name: CourtPointArea_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tenis
--

SELECT pg_catalog.setval('public."CourtPointArea_id_seq"', 3, true);


--
-- TOC entry 3392 (class 0 OID 0)
-- Dependencies: 213
-- Name: CourtType_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tenis
--

SELECT pg_catalog.setval('public."CourtType_id_seq"', 3, true);


--
-- TOC entry 3393 (class 0 OID 0)
-- Dependencies: 217
-- Name: Court_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tenis
--

SELECT pg_catalog.setval('public."Court_id_seq"', 1, true);


--
-- TOC entry 3394 (class 0 OID 0)
-- Dependencies: 209
-- Name: Player_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tenis
--

SELECT pg_catalog.setval('public."Player_id_seq"', 1, true);


--
-- TOC entry 3395 (class 0 OID 0)
-- Dependencies: 221
-- Name: PlayingData_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tenis
--

SELECT pg_catalog.setval('public."PlayingData_id_seq"', 1, false);


--
-- TOC entry 3396 (class 0 OID 0)
-- Dependencies: 211
-- Name: Stream_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tenis
--

SELECT pg_catalog.setval('public."Stream_id_seq"', 2, true);


--
-- TOC entry 3397 (class 0 OID 0)
-- Dependencies: 219
-- Name: aostype_id_seq; Type: SEQUENCE SET; Schema: public; Owner: tenis
--

SELECT pg_catalog.setval('public.aostype_id_seq', 3, true);


--
-- TOC entry 3223 (class 2606 OID 24642)
-- Name: AOSType aostype_pk; Type: CONSTRAINT; Schema: public; Owner: tenis
--

ALTER TABLE ONLY public."AOSType"
    ADD CONSTRAINT aostype_pk PRIMARY KEY (id);


--
-- TOC entry 3221 (class 2606 OID 24627)
-- Name: Court court_pk; Type: CONSTRAINT; Schema: public; Owner: tenis
--

ALTER TABLE ONLY public."Court"
    ADD CONSTRAINT court_pk PRIMARY KEY (id);


--
-- TOC entry 3219 (class 2606 OID 24617)
-- Name: CourtPointArea courtpointarea_pk; Type: CONSTRAINT; Schema: public; Owner: tenis
--

ALTER TABLE ONLY public."CourtPointArea"
    ADD CONSTRAINT courtpointarea_pk PRIMARY KEY (id);


--
-- TOC entry 3217 (class 2606 OID 24607)
-- Name: CourtType courttype_pk; Type: CONSTRAINT; Schema: public; Owner: tenis
--

ALTER TABLE ONLY public."CourtType"
    ADD CONSTRAINT courttype_pk PRIMARY KEY (id);


--
-- TOC entry 3213 (class 2606 OID 24586)
-- Name: Player player_pk; Type: CONSTRAINT; Schema: public; Owner: tenis
--

ALTER TABLE ONLY public."Player"
    ADD CONSTRAINT player_pk PRIMARY KEY (id);


--
-- TOC entry 3225 (class 2606 OID 24657)
-- Name: PlayingData playingdata_pk; Type: CONSTRAINT; Schema: public; Owner: tenis
--

ALTER TABLE ONLY public."PlayingData"
    ADD CONSTRAINT playingdata_pk PRIMARY KEY (id);


--
-- TOC entry 3215 (class 2606 OID 24597)
-- Name: Stream stream_pk; Type: CONSTRAINT; Schema: public; Owner: tenis
--

ALTER TABLE ONLY public."Stream"
    ADD CONSTRAINT stream_pk PRIMARY KEY (id);


--
-- TOC entry 3227 (class 2606 OID 24643)
-- Name: AOSType aostype_fk; Type: FK CONSTRAINT; Schema: public; Owner: tenis
--

ALTER TABLE ONLY public."AOSType"
    ADD CONSTRAINT aostype_fk FOREIGN KEY (court_point_area_id) REFERENCES public."CourtPointArea"(id) ON UPDATE RESTRICT ON DELETE RESTRICT;


--
-- TOC entry 3226 (class 2606 OID 24628)
-- Name: Court court_fk; Type: FK CONSTRAINT; Schema: public; Owner: tenis
--

ALTER TABLE ONLY public."Court"
    ADD CONSTRAINT court_fk FOREIGN KEY (court_type_id) REFERENCES public."CourtType"(id) ON UPDATE RESTRICT ON DELETE RESTRICT;


--
-- TOC entry 3228 (class 2606 OID 24658)
-- Name: PlayingData playingdata_fk; Type: FK CONSTRAINT; Schema: public; Owner: tenis
--

ALTER TABLE ONLY public."PlayingData"
    ADD CONSTRAINT playingdata_fk FOREIGN KEY (player_id) REFERENCES public."Player"(id) ON UPDATE RESTRICT ON DELETE RESTRICT;


--
-- TOC entry 3229 (class 2606 OID 24663)
-- Name: PlayingData playingdata_fk_1; Type: FK CONSTRAINT; Schema: public; Owner: tenis
--

ALTER TABLE ONLY public."PlayingData"
    ADD CONSTRAINT playingdata_fk_1 FOREIGN KEY (court_id) REFERENCES public."Court"(id) ON UPDATE RESTRICT ON DELETE RESTRICT;


--
-- TOC entry 3230 (class 2606 OID 24668)
-- Name: PlayingData playingdata_fk_2; Type: FK CONSTRAINT; Schema: public; Owner: tenis
--

ALTER TABLE ONLY public."PlayingData"
    ADD CONSTRAINT playingdata_fk_2 FOREIGN KEY (aos_type_id) REFERENCES public."AOSType"(id) ON UPDATE RESTRICT ON DELETE RESTRICT;


--
-- TOC entry 3231 (class 2606 OID 24673)
-- Name: PlayingData playingdata_fk_3; Type: FK CONSTRAINT; Schema: public; Owner: tenis
--

ALTER TABLE ONLY public."PlayingData"
    ADD CONSTRAINT playingdata_fk_3 FOREIGN KEY (stream_id) REFERENCES public."Stream"(id) ON UPDATE RESTRICT ON DELETE RESTRICT;


-- Completed on 2022-06-27 13:03:25 +03

--
-- PostgreSQL database dump complete
--

