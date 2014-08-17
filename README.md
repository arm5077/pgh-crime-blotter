openblotter
=================

Scrapes, stores and and displays Pittsburgh Bureau of Police incident data.

Background
----
Every morning (usually), the Pittsburgh police department publishes a PDF of the previous day's incidents and arrests here: [http://communitysafety.pittsburghpa.gov/Blotter.aspx](http://communitysafety.pittsburghpa.gov/Blotter.aspx). Trouble is, they're posted in tough-to-read PDFs.

Openblotter scrapes these PDFs, inserts relevant information into a PostgreSQL database and serves it all up on a spiffy map. 

Setup
-----

### Requirements
* Apache or other web server
* Python enabled on that web server
* A PostgreSQL database

### Python dependencies
* [Psycopg](http://initd.org/psycopg/)
* [PDFMiner](http://www.unixuser.org/~euske/python/pdfminer/#install)

### Installation
_These instructions assume you're using an httpd/Apache web server program._
1. Download the repository and store in `/var/html/www`.
2. Run `sql/initialize.sql` in PostgreSQL to set up `incident` and `incidentdescription` tables using the schema shown below.
3. Add your PostgreSQL login credentials to `py/contants.py`.
4. Install required libraries
  * `sudo pip install psycopg2` (Don't forget psycopg's dependencies, `python-dev` and `libpq-dev`. [Check notes here.](http://initd.org/psycopg/install/#installing-from-source-code))
  * `sudo pip install pdfminer`
5. Set up a cronjob to run `py/parser.py` at regular intervals. (Example: `00 09,11,13,18 * * * /usr/bin/python /var/www/html/blotter/py/parser.py`)
6. [Profit!](https://www.youtube.com/watch?v=tO5sxLapAts)

Errors and logs
----

Openblotter maintains an error log of misread (and therefore unincluded) entries at `txt/errors.txt`.

Each pre-scraped PDF is stored as `pdf/YYYYMMDD.pdf`.

Each just-converted text file is stored as `txt/YYYYMMDD.txt`.

Database schema
----

Openblotter's schema includes two tables: `incident`, which stores metadata (time, location, neighborhood) about a given event, and `incidentdescription`, which lists the various crimes associated with each event.

### incident

<table>
	<thead>
		<tr>
			<th>Field</th>
			<th>Type</th>
			<th>Purpose</th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td>incidentid</td>
			<td>serial integer</td>
			<td>Unique ID associated with each incident</td>
		</tr>
		<tr>
			<td>incidenttype</td>
			<td>character</td>
			<td>Type of incident: `Arrest` or `Offense 2.0`</td>
		</tr>
		<tr>
			<td>incidentnumber</td>
			<td>integer</td>
			<td>ID assigned to incident by police</td>
		</tr>
		<tr>
			<td>incidentdate</td>
			<td>date</td>
			<td>Date of incident</td>
		</tr>
		<tr>
			<td>incidenttime</td>
			<td>time without timezone</td>
			<td>Time of incident</td>
		</tr>
		<tr>
			<td>address</td>
			<td>character</td>
			<td>Address of incident (as reported by police, not geocoded)</td>
		</tr>
		<tr>
			<td>neighborhood</td>
			<td>character</td>
			<td>Neighborhood of incident (as reported by police, not geocoded)</td>
		</tr>
		<tr>
			<td>lat</td>
			<td>numeric</td>
			<td>Latitude of incident (geocoded from address and neighborhood)</td>
		</tr>
		<tr>
			<td>lng</td>
			<td>numeric</td>
			<td>Longitude of incident (geocoded from address and neighborhood)</td>
		</tr>
		<tr>
			<td>Zone</td>
			<td>character</td>
			<td>Police zone responding to incident (not always the same as the zone where the incident took place</td>
		</tr>
		<tr>
			<td>age</td>
			<td>smallint</td>
			<td>Age of suspect (if `incidenttype` is `Arrest`)</td>
		</tr>
		<tr>
			<td>Gender</td>
			<td>character</td>
			<td>Gender of suspect (if `incidenttype` is `Arrest`)</td>
		</tr>
		<tr>
			<td>geom</td>
			<td>geometry(Point, 4326)</td>
			<td>Geometry of incident, derived from `lat`/`lng`</td>
		</tr>
	</tbody>
</table>

### incidentdescription

<table>
	<thead>
		<tr>
			<th>Field</th>
			<th>Type</th>
			<th>Purpose</th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td>incidentdescriptionid</td>
			<td>serial integer</td>
			<td>Unique ID associated with each incident charge</td>
		</tr>
		<tr>
			<td>incidentid</td>
			<td>integer</td>
			<td>Unique ID associated with each incident; links to `incident` table</td>
		</tr>
		<tr>
			<td>section</td>
			<td>character</td>
			<td>Section of the this charge's criminal statute</td>
		<tr>
			<td>description</td>
			<td>character</td>
			<td>Text description of charge</td>
		</tr>
		
		
	</tbody>
</table>