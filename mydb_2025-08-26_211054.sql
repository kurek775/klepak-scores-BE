--
-- PostgreSQL database dump
--

\restrict USdOswZVsodklRMgAB1uXahxHJlRo1ElEUrXKlY4nCgBrekykmNsiOFwrovkSEY

-- Dumped from database version 17.2 (Debian 17.2-1.pgdg120+1)
-- Dumped by pg_dump version 17.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: crew_leaders; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.crew_leaders (
    crew_id integer NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.crew_leaders OWNER TO myuser;

--
-- Name: crews; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.crews (
    id integer NOT NULL,
    number integer,
    tour_id integer
);


ALTER TABLE public.crews OWNER TO myuser;

--
-- Name: COLUMN crews.tour_id; Type: COMMENT; Schema: public; Owner: myuser
--

COMMENT ON COLUMN public.crews.tour_id IS 'FK to tours.id (the tour this crew belongs to)';


--
-- Name: crews_id_seq; Type: SEQUENCE; Schema: public; Owner: myuser
--

CREATE SEQUENCE public.crews_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.crews_id_seq OWNER TO myuser;

--
-- Name: crews_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: myuser
--

ALTER SEQUENCE public.crews_id_seq OWNED BY public.crews.id;


--
-- Name: persons; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.persons (
    id integer NOT NULL,
    name character varying,
    crew_id integer
);


ALTER TABLE public.persons OWNER TO myuser;

--
-- Name: persons_id_seq; Type: SEQUENCE; Schema: public; Owner: myuser
--

CREATE SEQUENCE public.persons_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.persons_id_seq OWNER TO myuser;

--
-- Name: persons_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: myuser
--

ALTER SEQUENCE public.persons_id_seq OWNED BY public.persons.id;


--
-- Name: results; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.results (
    id integer NOT NULL,
    tour_id integer NOT NULL,
    sport_id integer NOT NULL,
    person_id integer NOT NULL,
    score double precision
);


ALTER TABLE public.results OWNER TO myuser;

--
-- Name: results_id_seq; Type: SEQUENCE; Schema: public; Owner: myuser
--

CREATE SEQUENCE public.results_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.results_id_seq OWNER TO myuser;

--
-- Name: results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: myuser
--

ALTER SEQUENCE public.results_id_seq OWNED BY public.results.id;


--
-- Name: sports; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.sports (
    id integer NOT NULL,
    name character varying NOT NULL,
    metric character varying
);


ALTER TABLE public.sports OWNER TO myuser;

--
-- Name: sports_id_seq; Type: SEQUENCE; Schema: public; Owner: myuser
--

CREATE SEQUENCE public.sports_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sports_id_seq OWNER TO myuser;

--
-- Name: sports_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: myuser
--

ALTER SEQUENCE public.sports_id_seq OWNED BY public.sports.id;


--
-- Name: templates; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.templates (
    id integer NOT NULL,
    "bgImage" bytea,
    font bytea,
    "textPosition" character varying
);


ALTER TABLE public.templates OWNER TO myuser;

--
-- Name: templates_id_seq; Type: SEQUENCE; Schema: public; Owner: myuser
--

CREATE SEQUENCE public.templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.templates_id_seq OWNER TO myuser;

--
-- Name: templates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: myuser
--

ALTER SEQUENCE public.templates_id_seq OWNED BY public.templates.id;


--
-- Name: tour_sports; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.tour_sports (
    tour_id integer NOT NULL,
    sport_id integer NOT NULL,
    "position" integer,
    is_optional boolean DEFAULT false
);


ALTER TABLE public.tour_sports OWNER TO myuser;

--
-- Name: tours; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.tours (
    id integer NOT NULL,
    year integer,
    part character varying,
    theme character varying,
    template_id integer
);


ALTER TABLE public.tours OWNER TO myuser;

--
-- Name: tours_id_seq; Type: SEQUENCE; Schema: public; Owner: myuser
--

CREATE SEQUENCE public.tours_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tours_id_seq OWNER TO myuser;

--
-- Name: tours_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: myuser
--

ALTER SEQUENCE public.tours_id_seq OWNED BY public.tours.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying NOT NULL,
    name character varying,
    picture_url text,
    is_admin boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    last_login_at timestamp without time zone,
    sub character varying(255)
);


ALTER TABLE public.users OWNER TO myuser;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: myuser
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO myuser;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: myuser
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: crews id; Type: DEFAULT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.crews ALTER COLUMN id SET DEFAULT nextval('public.crews_id_seq'::regclass);


--
-- Name: persons id; Type: DEFAULT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.persons ALTER COLUMN id SET DEFAULT nextval('public.persons_id_seq'::regclass);


--
-- Name: results id; Type: DEFAULT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.results ALTER COLUMN id SET DEFAULT nextval('public.results_id_seq'::regclass);


--
-- Name: sports id; Type: DEFAULT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.sports ALTER COLUMN id SET DEFAULT nextval('public.sports_id_seq'::regclass);


--
-- Name: templates id; Type: DEFAULT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.templates ALTER COLUMN id SET DEFAULT nextval('public.templates_id_seq'::regclass);


--
-- Name: tours id; Type: DEFAULT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.tours ALTER COLUMN id SET DEFAULT nextval('public.tours_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: crew_leaders; Type: TABLE DATA; Schema: public; Owner: myuser
--

COPY public.crew_leaders (crew_id, user_id) FROM stdin;
1	2
2	4
2	5
3	6
3	7
1	3
\.


--
-- Data for Name: crews; Type: TABLE DATA; Schema: public; Owner: myuser
--

COPY public.crews (id, number, tour_id) FROM stdin;
1	1	1
2	2	1
3	3	2
\.


--
-- Data for Name: persons; Type: TABLE DATA; Schema: public; Owner: myuser
--

COPY public.persons (id, name, crew_id) FROM stdin;
1	John Smith	1
2	Emily Davis	1
3	Michael Brown	1
4	Sarah Wilson	1
5	David Taylor	1
6	Laura Thomas	1
7	James Moore	1
8	Anna Jackson	1
9	Robert White	1
10	Linda Harris	1
11	Chris Martin	2
12	Sophia Clark	2
13	Daniel Lewis	2
14	Olivia Young	2
15	Matthew Hall	2
16	Grace Allen	2
17	Anthony King	2
18	Ella Scott	2
19	Joshua Green	2
20	Chloe Baker	2
21	Benjamin Adams	3
22	Victoria Nelson	3
23	Samuel Carter	3
24	Isabella Mitchell	3
25	Alexander Perez	3
26	Mia Roberts	3
27	William Turner	3
28	Ava Phillips	3
29	Joseph Campbell	3
30	Sofia Parker	3
\.


--
-- Data for Name: results; Type: TABLE DATA; Schema: public; Owner: myuser
--

COPY public.results (id, tour_id, sport_id, person_id, score) FROM stdin;
1	1	1	1	12.5
2	1	1	2	13.2
3	1	1	3	14
4	1	1	4	15.3
5	1	1	5	13.8
6	1	1	6	14.5
7	1	1	7	12.9
8	1	1	8	13.7
9	1	1	9	14.2
10	1	1	10	15
11	1	1	11	12.7
12	1	1	12	13.5
13	1	1	13	14.1
14	1	1	14	15.2
15	1	1	15	13.9
16	1	1	16	14.3
17	1	1	17	12.8
18	1	1	18	13.4
19	1	1	19	14
20	1	1	20	15.1
21	1	1	21	12.6
22	1	1	22	13.3
23	1	1	23	14.2
24	1	1	24	15.4
25	1	1	25	13.7
26	1	1	26	14.6
27	1	1	27	12.9
28	1	1	28	13.6
29	1	1	29	14.3
30	1	1	30	15
31	1	2	1	55.2
32	1	2	2	57.8
33	1	2	3	60.1
34	1	2	4	59.5
35	1	2	5	58.3
36	1	2	6	61
37	1	2	7	56.7
38	1	2	8	58.8
39	1	2	9	59.9
40	1	2	10	60.5
41	1	2	11	55.6
42	1	2	12	57.9
43	1	2	13	60.2
44	1	2	14	59.4
45	1	2	15	58.6
46	1	2	16	61.1
47	1	2	17	56.4
48	1	2	18	58.5
49	1	2	19	60
50	1	2	20	60.8
51	1	2	21	55.9
52	1	2	22	57.7
53	1	2	23	59.8
54	1	2	24	59.6
55	1	2	25	58.2
56	1	2	26	61.3
57	1	2	27	56.8
58	1	2	28	58.4
59	1	2	29	60.4
60	1	2	30	60.7
61	1	3	1	25.4
62	1	3	2	27.1
63	1	3	3	26.8
64	1	3	4	24.9
65	1	3	5	25.7
66	1	3	6	26.5
67	1	3	7	27
68	1	3	8	25.6
69	1	3	9	26.2
70	1	3	10	24.8
71	1	3	11	25.9
72	1	3	12	27.2
73	1	3	13	26.7
74	1	3	14	24.7
75	1	3	15	25.5
76	1	3	16	26.4
77	1	3	17	27.3
78	1	3	18	25.8
79	1	3	19	26.1
80	1	3	20	24.6
81	1	3	21	25.3
82	1	3	22	27.4
83	1	3	23	26.6
84	1	3	24	24.5
85	1	3	25	25.1
86	1	3	26	26.3
87	1	3	27	27.5
88	1	3	28	25
89	1	3	29	26
90	1	3	30	24.4
91	1	4	1	85
92	1	4	2	90
93	1	4	3	78
94	1	4	4	82
95	1	4	5	88
96	1	4	6	79
97	1	4	7	91
98	1	4	8	87
99	1	4	9	84
100	1	4	10	80
101	1	4	11	86
102	1	4	12	89
103	1	4	13	77
104	1	4	14	83
105	1	4	15	85
106	1	4	16	78
107	1	4	17	92
108	1	4	18	86
109	1	4	19	84
110	1	4	20	81
111	1	4	21	87
112	1	4	22	90
113	1	4	23	79
114	1	4	24	82
115	1	4	25	88
116	1	4	26	80
117	1	4	27	91
118	1	4	28	85
119	1	4	29	83
120	1	4	30	81
\.


--
-- Data for Name: sports; Type: TABLE DATA; Schema: public; Owner: myuser
--

COPY public.sports (id, name, metric) FROM stdin;
1	Running	time
2	Swimming	time
3	Cycling	distance
4	Archery	points
5	Super	distance
\.


--
-- Data for Name: templates; Type: TABLE DATA; Schema: public; Owner: myuser
--

COPY public.templates (id, "bgImage", font, "textPosition") FROM stdin;
\.


--
-- Data for Name: tour_sports; Type: TABLE DATA; Schema: public; Owner: myuser
--

COPY public.tour_sports (tour_id, sport_id, "position", is_optional) FROM stdin;
1	1	\N	f
1	2	\N	f
1	3	\N	f
1	4	\N	f
1	5	\N	f
\.


--
-- Data for Name: tours; Type: TABLE DATA; Schema: public; Owner: myuser
--

COPY public.tours (id, year, part, theme, template_id) FROM stdin;
1	2025	Summer	Annual Games	\N
2	2026	Winter	Super	\N
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: myuser
--

COPY public.users (id, email, name, picture_url, is_admin, created_at, last_login_at, sub) FROM stdin;
9	pavelkurek7@gmail.com	Pavel Kurek	https://lh3.googleusercontent.com/a/ACg8ocJzHqWziQ0An98eO7iZS1puwPPR1MjWrcT7rACoxBMygHn-jak=s96-c	f	2025-08-23 18:48:45.950709	2025-08-26 17:36:47.955157	110522246869664845806
10	kurekkurek53@gmail.com	KUREK KUREK	https://lh3.googleusercontent.com/a/ACg8ocIhsWCXRodahF0dW47JeO-bFSWwuICkdsUMFuJ0g93av4NcbA=s96-c	t	2025-08-23 18:50:28.005719	2025-08-26 17:37:13.78396	115115830378303873530
2	leader1@example.com	Alice Leader	d	f	2025-08-15 02:46:19.283585	2025-08-26 17:36:47.955157	2
3	leader2@example.com	Bob Leader	d	f	2025-08-15 02:46:19.283585	2025-08-26 17:36:47.955157	3
4	leader3@example.com	Charlie Leader	dd	f	2025-08-15 02:46:19.283585	2025-08-26 17:36:47.955157	443
5	leader4@example.com	Diana Leader	dd	f	2025-08-15 02:46:19.283585	2025-08-26 17:36:47.955157	32233
6	leader5@example.com	Ethan Leader	ddd	f	2025-08-15 02:46:19.283585	2025-08-26 17:36:47.955157	322233
7	leader6@example.com	Fiona Leader	ddddd	f	2025-08-15 02:46:19.283585	2025-08-26 17:36:47.955157	55544
\.


--
-- Name: crews_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.crews_id_seq', 3, true);


--
-- Name: persons_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.persons_id_seq', 30, true);


--
-- Name: results_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.results_id_seq', 120, true);


--
-- Name: sports_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.sports_id_seq', 5, true);


--
-- Name: templates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.templates_id_seq', 1, false);


--
-- Name: tours_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.tours_id_seq', 2, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: myuser
--

SELECT pg_catalog.setval('public.users_id_seq', 10, true);


--
-- Name: crew_leaders crew_leaders_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.crew_leaders
    ADD CONSTRAINT crew_leaders_pkey PRIMARY KEY (crew_id, user_id);


--
-- Name: crews crews_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.crews
    ADD CONSTRAINT crews_pkey PRIMARY KEY (id);


--
-- Name: persons persons_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.persons
    ADD CONSTRAINT persons_pkey PRIMARY KEY (id);


--
-- Name: results results_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.results
    ADD CONSTRAINT results_pkey PRIMARY KEY (id);


--
-- Name: results results_tour_id_sport_id_person_id_key; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.results
    ADD CONSTRAINT results_tour_id_sport_id_person_id_key UNIQUE (tour_id, sport_id, person_id);


--
-- Name: sports sports_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.sports
    ADD CONSTRAINT sports_pkey PRIMARY KEY (id);


--
-- Name: templates templates_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.templates
    ADD CONSTRAINT templates_pkey PRIMARY KEY (id);


--
-- Name: tour_sports tour_sports_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.tour_sports
    ADD CONSTRAINT tour_sports_pkey PRIMARY KEY (tour_id, sport_id);


--
-- Name: tours tours_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.tours
    ADD CONSTRAINT tours_pkey PRIMARY KEY (id);


--
-- Name: sports uq_sports_name; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.sports
    ADD CONSTRAINT uq_sports_name UNIQUE (name);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_crews_tour_id; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_crews_tour_id ON public.crews USING btree (tour_id);


--
-- Name: idx_persons_crew_id; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_persons_crew_id ON public.persons USING btree (crew_id);


--
-- Name: idx_results_person; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_results_person ON public.results USING btree (person_id);


--
-- Name: idx_results_tour_sport; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_results_tour_sport ON public.results USING btree (tour_id, sport_id);


--
-- Name: idx_tour_sports_sport; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_tour_sports_sport ON public.tour_sports USING btree (sport_id);


--
-- Name: idx_tour_sports_tour; Type: INDEX; Schema: public; Owner: myuser
--

CREATE INDEX idx_tour_sports_tour ON public.tour_sports USING btree (tour_id);


--
-- Name: crew_leaders crew_leaders_crew_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.crew_leaders
    ADD CONSTRAINT crew_leaders_crew_id_fkey FOREIGN KEY (crew_id) REFERENCES public.crews(id) ON DELETE CASCADE;


--
-- Name: crew_leaders crew_leaders_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.crew_leaders
    ADD CONSTRAINT crew_leaders_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: crews fk_crews_tour; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.crews
    ADD CONSTRAINT fk_crews_tour FOREIGN KEY (tour_id) REFERENCES public.tours(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: persons persons_crew_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.persons
    ADD CONSTRAINT persons_crew_id_fkey FOREIGN KEY (crew_id) REFERENCES public.crews(id) ON DELETE SET NULL;


--
-- Name: results results_person_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.results
    ADD CONSTRAINT results_person_id_fkey FOREIGN KEY (person_id) REFERENCES public.persons(id) ON DELETE CASCADE;


--
-- Name: results results_tour_id_sport_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.results
    ADD CONSTRAINT results_tour_id_sport_id_fkey FOREIGN KEY (tour_id, sport_id) REFERENCES public.tour_sports(tour_id, sport_id) ON DELETE CASCADE;


--
-- Name: tour_sports tour_sports_sport_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.tour_sports
    ADD CONSTRAINT tour_sports_sport_id_fkey FOREIGN KEY (sport_id) REFERENCES public.sports(id) ON DELETE RESTRICT;


--
-- Name: tour_sports tour_sports_tour_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.tour_sports
    ADD CONSTRAINT tour_sports_tour_id_fkey FOREIGN KEY (tour_id) REFERENCES public.tours(id) ON DELETE CASCADE;


--
-- Name: tours tours_template_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.tours
    ADD CONSTRAINT tours_template_id_fkey FOREIGN KEY (template_id) REFERENCES public.templates(id) ON DELETE SET NULL;


--
-- PostgreSQL database dump complete
--

\unrestrict USdOswZVsodklRMgAB1uXahxHJlRo1ElEUrXKlY4nCgBrekykmNsiOFwrovkSEY

