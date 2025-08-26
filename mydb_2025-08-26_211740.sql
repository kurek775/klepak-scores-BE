--
-- PostgreSQL database dump
--

\restrict x8wVDvZjpJo7jbdbf97x0OljXEWcDFcU8c6rCbehHVClHPJFEZvSmcnvEHe8Ba6

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

\unrestrict x8wVDvZjpJo7jbdbf97x0OljXEWcDFcU8c6rCbehHVClHPJFEZvSmcnvEHe8Ba6

