--
-- PostgreSQL database dump. Deze werkt niet goed, zie
-- http://public.deltares.nl/display/FEWSDOC/Rdbms+Export voor een
-- werkende.

--
-- TOC entry 1483 (class 1259 OID 195810)
-- Dependencies: 1764 1765 1766 3
-- Name: filter; Type: TABLE; Schema: public; Owner: postgres; Tablespace:
--

DROP TABLE filter;
DROP TABLE location;
DROP TABLE parameter;
DROP TABLE timeserie;
DROP TABLE timeseriedata;

CREATE TABLE filter (
    fkey integer NOT NULL,
    id character varying(64) NOT NULL,
    name character varying(256) DEFAULT NULL,
    description character varying(256) DEFAULT NULL,
    issubfilter integer,
    parentfkey integer,
    isendnode integer,
    PRIMARY KEY (fkey),
    UNIQUE (id),
    FOREIGN KEY (parentfkey) REFERENCES filter(fkey)
);


--
-- TOC entry 1482 (class 1259 OID 195797)
-- Dependencies: 1758 1759 1760 1761 1762 1763 3
-- Name: location; Type: TABLE; Schema: public; Owner: postgres; Tablespace:
--

CREATE TABLE location (
    lkey integer NOT NULL,
    id character varying(64) NOT NULL,
    name character varying(256) DEFAULT NULL,
    parentid character varying(64) DEFAULT NULL,
    description character varying(256) DEFAULT NULL,
    shortname character varying(256) DEFAULT NULL,
    tooltiptext character varying(1000) DEFAULT NULL,
    x double precision,
    y double precision,
    z double precision,
    longitude double precision,
    latitude double precision,
    PRIMARY KEY (lkey),
    UNIQUE (id)
);


--
-- TOC entry 1481 (class 1259 OID 195784)
-- Dependencies: 1752 1753 1754 1755 1756 1757 3
-- Name: parameter; Type: TABLE; Schema: public; Owner: postgres; Tablespace:
--

CREATE TABLE parameter (
    pkey integer NOT NULL,
    id character varying(64) NOT NULL,
    name character varying(256) DEFAULT NULL,
    shortname character varying(256) DEFAULT NULL,
    unit character varying(64) DEFAULT NULL,
    parametertype character varying(64) DEFAULT NULL,
    parametergroup character varying(64) DEFAULT NULL,
    PRIMARY KEY (pkey),
    UNIQUE (id)
);


--
-- TOC entry 1484 (class 1259 OID 195825)
-- Dependencies: 1767 3
-- Name: timeserie; Type: TABLE; Schema: public; Owner: postgres; Tablespace:
--

CREATE TABLE timeserie (
    tkey integer NOT NULL,
    moduleinstanceid character varying(64) NOT NULL,
    timestep character varying(64) NOT NULL,
    filterkey integer NOT NULL,
    locationkey integer NOT NULL,
    parameterkey integer NOT NULL,
    PRIMARY KEY (tkey),
    UNIQUE (locationkey, parameterkey, filterkey, moduleinstanceid, timestep),
    FOREIGN KEY (filterkey) REFERENCES filter(fkey),
    FOREIGN KEY (locationkey) REFERENCES location(lkey),
    FOREIGN KEY (parameterkey) REFERENCES parameter(pkey)
);

--
-- TOC entry 1485 (class 1259 OID 195848)
-- Dependencies: 1768 1769 1770 3
-- Name: timeseriedata; Type: TABLE; Schema: public; Owner: postgres; Tablespace:
--

CREATE TABLE timeseriedata (
    tkey integer NOT NULL,
    tsd_time timestamp without time zone NOT NULL,
    tsd_value double precision,
    tsd_flag character varying(1) DEFAULT NULL,
    tsd_detection character varying(1) DEFAULT NULL,
    tsd_comments character varying(256) DEFAULT NULL,
    PRIMARY KEY (tkey, tsd_time),
    FOREIGN KEY (tkey) REFERENCES timeserie(tkey)
);


