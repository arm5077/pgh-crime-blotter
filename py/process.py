#!/usr/bin/python

import cgi
import psycopg2
import json
import cgitb
cgitb.enable()	

def getAggregate():
	cur.execute( """SELECT
						incidentdescription.description as description, COUNT(incidentdescription.incidentdescriptionid) as total
						FROM blotter.incidentdescription
						JOIN blotter.incident on incident.incidentid = incidentdescription.incidentid
						WHERE incident.incidentdate BETWEEN %s AND %s
						GROUP BY blotter.incidentdescription.description
						ORDER BY total DESC
						
	""", (fields["startDate"].value, fields["endDate"].value))
	results = cur.fetchall()
	
	export_array = []
	for aggregateCharge in results:
		export_array.append({"description": aggregateCharge[0], "total": aggregateCharge[1]})
	print 'Content-type: text/html\n\n'
	#print "Content-type:application/json\r\n\r\n" 		
	print json.dumps(export_array)

def getIncidents():
	cur.execute( """SELECT 
						incidentid, 
						incidenttype,
						incidentdate,
						incidenttime,
						address,
						neighborhood,
						lat,
						lng,
						zone,
						age,
						gender
					FROM blotter.incident 
					WHERE incidentdate BETWEEN %s AND %s 
				""", ( fields["startDate"].value, fields["endDate"].value ) )
	results = cur.fetchall()
	
	
	export_array = []
	for incident in results:
	
		# Search for charges/descriptions in each ID
		cur.execute( """SELECT
							incidentdescriptionid,
							incidentid,
							section,
							description
						FROM blotter.incidentdescription
						WHERE incidentid = %s
		""", ( [incident[0]] ))
		charges = cur.fetchall()
		
		charges_array = []
		for charge in charges:
			charges_array.append({
				"section": charge[2],
				"description": charge[3]
			})
		
		export_array.append({
			"type": incident[1],
			"date": str(incident[2]),
			"time": str(incident[3]),
			"address": incident[4],
			"neighborhood": incident[5],
			"lat": float(incident[6]),
			"lng": float(incident[7]),
			"zone": str(incident[8]),
			"age": incident[9],
			"gender": str(incident[10]),
			"charges": charges_array
		})
	print 'Content-type: text/html\n\n'
	#print "Content-type:application/json\r\n\r\n" 		
	print json.dumps(export_array)
	
# Connect to database and initialize cursor
conn = psycopg2.connect("host=blotter.ca5wksbwkzsv.us-east-1.rds.amazonaws.com dbname=blotter user=arm5077 password=lukebryan")
cur = conn.cursor()



operations = {"getIncidents": getIncidents, "getAggregate": getAggregate}

fields = cgi.FieldStorage()
operations[ fields["operation"].value ]()


# Close database cursor and connection
cur.close()
conn.close()

