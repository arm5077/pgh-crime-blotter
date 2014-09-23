# assumptions
# 1. all the zones are always represented, and there's at least one crime in every zone
# 2. there are 6 zones and 1 OSC zone
# 3. all charge sections have cooresponding charge descriptions
# 4. charge sections start with a number
# 5. if charge sections don't start with a number, they start with "misc" or "mental"

from constants import *
import os
import sys
import urllib2
import time
import re
import psycopg2
import json
from datetime import datetime, timedelta
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams

zones = ["Zone 1", "Zone 2", "Zone 3", "Zone 4", "Zone 5", "Zone 6", "Zone OSC"]
headers = ['Incident Time', 'Location of Occurrence', 'Neighborhood', 'Incident', 'Age', 'Gender', 'Section', 'Description']


###################temp
export = file("../txt/export.txt", "w+")
error_log = file("../txt/errors.txt", "a+")

def parsePDF(infile, outfile):
	
	password = ''
	pagenos = set()
	maxpages = 0
	# output option
	outtype = None
	imagewriter = None
	rotation = 0
	stripcontrol = False
	layoutmode = 'normal'
	codec = 'utf-8'
	pageno = 1
	scale = 1
	caching = True
	showpageno = True
	laparams = LAParams()
	rsrcmgr = PDFResourceManager(caching=caching)
	
	if outfile:
		outfp = file(outfile, 'w+')
	else:
		outfp = sys.stdout
	
	device = TextConverter(rsrcmgr, outfp, codec=codec, laparams=laparams, imagewriter=imagewriter)
	fp = file(infile, 'rb')
	interpreter = PDFPageInterpreter(rsrcmgr, device)
	for page in PDFPage.get_pages(fp, pagenos,
									  maxpages=maxpages, password=password,
									  caching=caching, check_extractable=True):
			
		interpreter.process_page(page)
	fp.close()
	device.close()
	outfp.close()
	return	

# Start of main code. Didn't put this in a "main" function since I'm not sure if you're using one

# Set time zone to EST
os.environ['TZ'] = 'America/New_York'
time.tzset()

# make sure folder system is set up
if not os.path.exists("../pdf/"):
	os.makedirs("../pdf/")
if not os.path.exists("../txt/"):
	os.makedirs("../txt/")

# Get yesterday's name and lowercase it
yesterday = (datetime.today() - timedelta(1))
yesterday_string = yesterday.strftime("%A").lower()

# Also make a numberical representation of date for filename purposes
yesterday_short = yesterday.strftime("%Y%m%d")

# Get pdf from blotter site, save it in a file
pdf = urllib2.urlopen("http://apps.pittsburghpa.gov/police/arrest_blotter/arrest_blotter_" + yesterday_string + ".pdf").read();
f = file("../pdf/" + yesterday_short + ".pdf", "w+")
f.write(pdf)
f.close()

# Convert pdf to text file
parsePDF("../pdf/" + yesterday_short + ".pdf", "../txt/" + yesterday_short + ".txt")

# Save text file contents in variable
parsed_pdf = file("../txt/" + yesterday_short + ".txt", "r").read()

# Get date
export_date = parsed_pdf[47:57]

# If pulled date doesn't match yesterday's date, kill the process
if export_date != yesterday.strftime("%m/%d/%Y"):
	print "Yesterday's PDF hasn't been posted yet."
	sys.exit()

# Clear "Page X of XX from document"
parsed_pdf = re.sub(re.compile(r"^Page.*", re.MULTILINE), "", parsed_pdf)

# Clear header at the top of every page
parsed_pdf = re.sub(re.compile(r"(PITTSBURGH BUREAU OF POLICE)(.*?)(on this site.\n)", re.MULTILINE|re.DOTALL), "", parsed_pdf)

# Find zones, leave first of each kind and delete the rest.
parsed_pdf = parsed_pdf.replace("Zone\n\n", "Zone ")
for zone in zones:
	start = parsed_pdf.find(zone)
	parsed_pdf = parsed_pdf[:start + len(zone)] + parsed_pdf[(start + len(zone)):].replace(zone, "")

# Clear page breaks
parsed_pdf = parsed_pdf.replace("\f", "")

# Convert Golden Triangle/Civic\nArena to Golden Triangle/Civic Arena
parsed_pdf = parsed_pdf.replace("Golden Triangle/Civic\nArena", "Golden Triangle/Civic Arena")

# Remove descriptive headers like "Description" and "Age."
# Since they're often cut off by the page header, 
# they're actually more trouble than they're worth.
for header in headers:
	parsed_pdf = parsed_pdf.replace(header + "\n", "")

# Remove extraneous spaces
for i in range(0,5):
	parsed_pdf = parsed_pdf.replace("\n\n", "\n")
parsed_pdf = parsed_pdf[1:]
parsed_pdf = parsed_pdf[:len(parsed_pdf) - 1]

####### temp
export.write(parsed_pdf)

# Begin conversion to array
	
# Split string by zones
parsed_array = re.split("Zone.*", parsed_pdf)

# Eliminate empty first item
parsed_array = parsed_array[1:]

# Parse individual zoness into separate incidents
for i,val in enumerate(parsed_array):
	parsed_array[i] = parsed_array[i].split("Report Name")
	
	# Eliminate empty lines at beginning
	parsed_array[i] = parsed_array[i][1:]
	
	# Split lines in incidents into array objects
	for j, val in enumerate(parsed_array[i]):
		parsed_array[i][j] = parsed_array[i][j].split("\n")
		
		# Eliminate empty lines at start and beginning
		if parsed_array[i][j][0] == "":
			parsed_array[i][j] = parsed_array[i][j][1:]
		if parsed_array[i][j][len(parsed_array[i][j]) - 1] == "":
			parsed_array[i][j] = parsed_array[i][j][:len(parsed_array[i][j]) - 1]
	
# Setting up array is now finished
			
# Connect to database
try:
	conn = psycopg2.connect(
		host = my_host, 
		database = my_database,
		user = my_user, 
		password = my_password, 
	)			
except Exception, e:
	print e
	sys.exit()

cur = conn.cursor()

# Check if incidents for this date have already been uploaded
cur.execute("SELECT COUNT(*) FROM blotter.incident WHERE incidentdate = %s", (export_date,))
if cur.fetchone()[0] > 0:
	print "Already have entries from today! Exiting now..."
	sys.exit()


# Cycle through zones
for i, zone in enumerate(parsed_array):
	
	# Set export zone variable to current zone
	export_zone = zones[i]
	
	for j, incident in enumerate(zone):
		export_type = incident[0].strip()
		
		# Grab incident time
		export_time = incident[1].strip()
		
		# Grab incident location 
		export_location = incident[2].strip()
		
		# Grab incident neighborhood
		export_neighborhood = incident[3].strip()
		
		# Geocode
		response = urllib2.urlopen("https://maps.googleapis.com/maps/api/geocode/json?address=" + urllib2.quote(export_location + "," + export_neighborhood + "," + "Pittsburgh,PA") + "&key=AIzaSyAAW6S-8jXwA7BTsufPFxIxRyH8Gn4luNM")
		json_geocode = response.read()
		json_geocode = json.loads(json_geocode)		
		if json_geocode["status"] == "OK":
			lat = json_geocode["results"][0]["geometry"]["location"]["lat"]
			lng = json_geocode["results"][0]["geometry"]["location"]["lng"]
		else:
			lat = None
			lng = None
		
		# Grab incident number
		export_number = incident[4].strip()
		
		# Check if incident is an arrest;
		# if so, the next few lines have suspect information
		if export_type == "ARREST":
			if incident[5].strip().isdigit():
				export_age = incident[5].strip()
				export_gender = incident[6].strip()
				start = 7
			else:
				export_gender = incident[5].strip()
				start = 6
		else: 
			export_age = None
			export_gender = None
			start = 5
		
		# Let's insert this incident info into the database
		try:
			cur.execute("""
						INSERT INTO blotter.incident
						(
							incidenttype,
							incidentnumber,
							incidentdate,
							incidenttime,
							address,
							neighborhood,
							lat,
							lng,
							zone,
							age,
							gender, 
							geom
						)
						VALUES
						(
							%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, ST_GeomFromText(%s, 4326)
						)
						RETURNING incidentid;
						""",
						( 
							export_type, 
							export_number, 
							export_date, 
							export_time, 
							export_location, 
							export_neighborhood, 
							lat,
							lng,
							export_zone, 
							export_age,
							export_gender,
							"POINT(" + str(lng) + " " + str(lat) + ")"
							
						) 
					)
					
			# Grab unique ID that was just 
			# generated for this incident
			# in our database
			incidentid = cur.fetchone()
		
		except Exception, e:
			print e
			error_log.write("ERROR ON INCIDENT(" + str(datetime.today()) + "): " + export_type + ": " + export_number + ", " + export_time + " -- " + str(e))
			conn.rollback()
			continue
		
		# OK, so this is fun. Essentially, the algorithm assumes that 
		# for the remaining lines, anything starting with a digit is a section number
		# (except for lines starting with "Misc. Incident" and "Mental"),
		# and anything starting otherwise is a description. I had a more elegant algorithm,  
		# but page breaks in the PDF can sometimes mess up the order of things. 
		export_section_array = []
		export_description_array = []
		
		for k in range(start, len(incident)):
			if incident[k][:1].isdigit() and 'Misc. Incident' not in incident[k] and 'Mental' not in incident[k]:
				export_section_array.append(incident[k])
			else:
				export_description_array.append(incident[k])

		# Add incident descriptions to database
		for l, val in enumerate(export_section_array):
			try:
				cur.execute("""
							INSERT INTO blotter.incidentdescription
							(
								incidentid,
								section,
								description
							)
							VALUES
							(
								%s, %s, %s
							)
							""",
							(
								incidentid,
								val,
								export_description_array[l]
							)
						)
			except Exception, e:
				print e
				error_log.write("ERROR ON INCIDENTDESCRIPTION(" + str(datetime.today()) + "): " + export_type + ": " + export_number + ", " + export_time + " -- " + str(e))
				conn.rollback()
				continue
		
		# Commit incident to database
		conn.commit()	

cur.close()
conn.close()
		