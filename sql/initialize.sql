/* Add postgis extensions (including TIGER geocoder, if we ever use that */
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;
CREATE EXTENSION IF NOT EXISTS postgis_tiger_geocoder;

/* Create blotter schema */
DROP SCHEMA IF EXISTS "blotter" CASCADE;
CREATE SCHEMA "blotter";

/* Create main incident table */
DROP TABLE IF EXISTS "blotter".incident;
CREATE TABLE "blotter".incident
(
  incidentid serial NOT NULL,
  incidenttype character varying(20),
  incidentnumber integer,
  incidentdate date,
  incidenttime time without time zone,
  address character varying(50),
  neighborhood character varying(30),
  lat decimal,
  lng decimal,
  zone character varying(10),
  age smallint,
  gender character(1),
  CONSTRAINT incident_pkey PRIMARY KEY (incidentid)
)
WITH (
  OIDS=FALSE
);

SELECT AddGeometryColumn( 'blotter', 'incident', 'geom', 4326, 'POINT', 2);

/* Create crimes-within-incident table */
DROP TABLE IF EXISTS "blotter".incidentdescription;
CREATE TABLE "blotter".incidentdescription
(
incidentdescriptionid serial NOT NULL,
incidentid integer,
section character varying(50),
description character varying(100),
CONSTRAINT incidentdescription_pkey PRIMARY KEY (incidentdescriptionid)
)
WITH (
	OIDS=FALSE
);
