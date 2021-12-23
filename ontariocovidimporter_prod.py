# Tom's Ontario Covid Report

## Import Modules 
from datetime import date
import json
import urllib.request as ur
import urllib.parse as prs
from datetime import datetime, timedelta
import sys
from sys import platform
import requests

# test

# Create logging function
## This function logs messages that are passed to it to a log file, along with a timestamp that the message was sent. 
def logit (event,dtime = 'no'):
	now = datetime.now()
	if dtime=='yes':
		logDateTime = now.strftime("%m/%d/%y - %H:%M:%S.%f")[:-5]
		dash = ' - '
	else:
		logDateTime = ''
		dash = '- '
	f = open('log.txt','a')
	f.write('\n'+logDateTime+dash+event)
	f.close()

# This section sets some variables based on arguments that were passed in when called from the command line.
## This variable records whether the script was called via cron job or not.
cron = ''



# Log that the job is starting. 
logit ("Starting script\n"+cron,'yes')


## Define some dates!
reporteddate = ''
getdate = date.today()# + timedelta(days=+1) #Uncomment the right section to point to tomorrow's date. To test instances where today's data is not available.
formattedToday = str(getdate.strftime('%m/%d'))
yesterday = getdate - timedelta(days=1)
fyesterday = str(yesterday.strftime('%m/%d'))
reportingdate = getdate.strftime("%B %d, %Y") # This is used to display the date the report was run

# This is a function to check a given file for a given term to see if it's there.
def checkfile(file_name, string_to_search):
    with open(file_name, 'r') as read_obj:
        # Read all lines in the file one by one
        for line in read_obj:
            if string_to_search in line:
                return True
    return False

## This checks which arguments were passed in.
## Passing in with an argument of 'yesterday' allows the script to check with yesterday's data for troubleshooting.
## Passing in with an argument of 'cron' should be done if triggering from a cron job. This will reflect in the log that the script was called via cron job.
if len(sys.argv) > 1:
	argslot = 1
	for i in sys.argv[1:]:
		if sys.argv[argslot] == 'yesterday':
			getdate = date.today() - timedelta(days=1)
			reporteddate = '**Yesterday\'s Data**',getdate
		elif sys.argv[argslot] == 'cron':
			cron = '(CRON)'
		argslot += 1

# Web Tokens
## This function gets a token from a given web service for authentication. This allows the tokens to be stored in a file separate from the script for security purposes. 
def keygetter(file):
	 f = open(file,'r')
	 return f.read()

## This is the token for the Buttondown service used for sending the newsletter.
BDToken = keygetter('BDToken.txt')
## This is the token for If This then That, which updates the Google sheet.
IFToken = keygetter('IFToken.txt')

# This function updates the Google Sheet with a given set of data (via IFTTT)
def gsheetupdate(date):
	hookurl = 'https://maker.ifttt.com/trigger/addsheet/with/key/'+IFToken
	payload = {
				"value1":str(coviddataset['total doses administered'][0])+'|'+str(coviddataset['total individuals fully vaccinated'][0]),"value2":str(coviddataset['Total Cases'][0])+'|'+str(coviddataset['Number of patients hospitalized with COVID-19'][0]),"value3":str(coviddataset['Number of patients in ICU due to COVID-19'][0])+'|'+str(date)
	}
	headers = {}
	res = requests.post(hookurl, data=payload, headers=headers)

# Email Stuff
## Section for setting variables that will be used for the newsletter. 
htmlstart = '<span style="color:'
htmlend = '</span>'
esubject = 'Tom\'s Ontario COVID Report for '+str(getdate.strftime('%B %d, %Y'))
emailbody = ''

# Define Query Parameters

## URL Query Variables - Universal
### These are the variables we will use to build our query.
urlstart = 'https://data.ontario.ca/api/3/action/datastore_search?'	
today = str(date.today())+'T00:00:00'
urlfilter = ''
fieldQuery = ''
resourceid = ''
friendlyname = '' 

## URL Query Variables - Per Dataset
### Each Ontario dataset has a unique resource ID that we use to identify it when querying.
resourceidlist = {
	'Vaccinedata': '8a89caa9-511c-4568-af89-7f2174b4378c',
	'Casedata': 'ed270bb8-340b-41f9-a7c6-e8ef587e6d11'
	}
### For some reason, each Ontario dataset seems to have a different field name for reported data. This specifies the correct date field name per dataset so we can query by date. 
datefieldlist = {
	'Vaccinedata': 'report_date',
	'Casedata': 'Reported Date'
	}
### This variable stores all of the fields we want to retrieve from each Ontario dataset. The script will get and print all of today's data for each field listed here.
fieldlist = {
	'Vaccinedata': ['total_doses_administered', 'total_individuals_fully_vaccinated', 'total_individuals_3doses'],
	'Casedata': ['Total Cases', 'Number of patients hospitalized with COVID-19','Number of patients in ICU due to COVID-19']
	}
## This specifies what we want to call each dataset when we output its results. 
friendlynamelist = {
	'Vaccinedata': 'Vaccine Data',
	'Casedata': 'Case Data'
	}

## Create a dictionary variable that will store the all the data that we retrieve
coviddataset = {}
## This little loop takes all of the fields we listed in 'field list' and adds them to the coviddataset dictionary variable as keys. We'l use this later to parse through and add values to.
for x in fieldlist:
	for i in fieldlist[x]:
		i = i.replace('_',' ')
		coviddataset[i] = []

## This variable will store the number of results we get to check if they are complete. It starts at 0.
resultstotal = 0

# Get Data Section

## This is the big complicated function that we will call to get the different datasets later. We pass in the dataset, how many dates we are getting, and the reporting date (today or another day). 
def getcoviddata(dataset,getdays,fetchdate):
	# Get dataset specific values for the query
	resourceid = resourceidlist[dataset]
	friendlyname = friendlynamelist[dataset]
	fields = fieldlist[dataset]
	urlfilter = '\"' + datefieldlist[dataset] + '\":'+ '['
	expectedresults = getdays
	#getdays = getdays + 1
	while getdays > 0:
		urlfilter = urlfilter + '\"' + str(fetchdate) + '\"'
		fetchdate = fetchdate - timedelta(days=1)
		getdays = getdays - 1
		if getdays > 0:
			urlfilter = urlfilter + ','
	urlfilter = urlfilter+']'
	urlfilter = urlfilter.replace(' ', '%20')
	fieldQuery = ''
	# Set global variables
	global resultstotal
	global coviddataset
	# clipboardresult = clipboardresult
	fields = fieldlist[dataset]
	## Create field list query section
	for x in fields[:-1]:
		fieldQuery = fieldQuery+'\''+x+'\','
	fieldQuery = fieldQuery+'\''+fields[len(fields)-1]+'\''
	fieldQuery = fieldQuery.replace(' ', '%20')
	fieldQuery = fieldQuery.replace('\'', '\"')
	# Make url
	queryurl = urlstart + 'resource_id=' + resourceid + '&fields=' + fieldQuery + '&filters={' + urlfilter + '}' + '&sort=\"' + datefieldlist[dataset] + '\"'
	queryurl = queryurl.replace(' ', '%20')
	logit(dataset+' url: '+queryurl)
	#print ('** ' + friendlynamelist[dataset] + ' Report *')
	url = queryurl
	fileobj = ur.urlopen(url)
	## Format Data Into Json
	gotdata = fileobj.read()
	nicedata = json.loads(gotdata)
	resultstotal = resultstotal + nicedata['result']['total']
	resultscheck = nicedata['result']['total']
	if resultscheck > 0:
		quay = resultscheck -1
		while quay > 0-1:
			for i in nicedata['result']['records'][quay]:
				recname = i
				recnum = nicedata['result']['records'][quay][i]
				recname = recname.replace('_', ' ')
				if type(recnum) == str:
					recnum = recnum.replace(',', '')
				# Add result to global dataset
				coviddataset[recname].append(recnum)
			quay = quay - 1

# Sets the parameters to determine the emoji to use based on how many arrows are pointing up. 
howrthings = {"0":"🥳","1":"😎","2":"🙂","3":"😐","4":"😕","5":"😨","6":"😱"}
gauge = 3
logit ('Starting gauge at '+str(gauge))
gaugefactor = []

# This variable keeps track of the factors and thresholds impacting the gauge
gaugethings = {
	'New Cases': {'threshold':0.1, 'name': 'New Cases', 'good': 'down'},
	'7 Day New Case Average': {'threshold': 0.02, 'name': '7 Day New Case Count', 'good':'down'},
	'Number of patients hospitalized with COVID-19': {'threshold': 0.1, 'name': 'Hospitalization Change', 'good': 'down'},
	'Number of patients in ICU due to COVID-19': {'threshold': 0.1, 'name': 'ICU Change', 'good': 'down'},
	'7 Day Hospital Change Average': {'threshold': 0.05, 'name': '7 Day Hospital Change Average', 'good': 'down'},
	'7 Day ICU Change Average': {'threshold': 0.05, 'name': '7 Day ICU Change Average', 'good': 'down'},
	'Maxxinated': {'threshold': 0.01, 'name': 'Percent Maxxinated', 'good': 'up'},
	'3 Shotters': {'threshold': 0.01, 'name': 'Percent 3 Shotters', 'good': 'up'},
	'7 Day Dose Average': {'threshold': 0.02, 'name': '7 Day Dose Average', 'good': 'up'},
	'7 Day Hopsital Average': {'threshold': 0.05, 'name': '7 Day Hopsital Average', 'good': 'down'},
	'7 Day ICU Average': {'threshold': 0.05, 'name': '7 Day ICU Average', 'good': 'down'},
	'People in Hospital + ICU': {'threshold': 0.05, 'name': '7 Day ICU Average', 'good': 'down'}
	}

# This function adjusts the gauge based on the factor and change fed into it
def gaugeit (change,factor):
	try:
		logit ('Gauge checking '+factor+' with a rate of '+str(round(change,2)))
		threshold = gaugethings[factor]['threshold']
		gaugeup = gaugethings[factor]['name'] + ' ' + 'up'
		direction = 'down'
		if gaugethings[factor]['good'] == 'up':
			change *= -1
			logit ('Up is good so '+factor+' is now '+str(round(change,2)))
		gaugedown = gaugethings[factor]['name'] + ' ' + gaugethings[factor]['good']
		global gauge
		if change < - threshold:
			if gaugethings[factor]['good'] == 'up':
				direction = 'up'
			else:
				direction = 'down'
			logit (factor+' matched below threshold')
			gauge -= 1
			logit ('Gauge is now '+str(gauge)+' - '+factor+' '+direction+'.\n')
			gaugefactor.append(factor+' '+direction+', ')
		elif change > threshold:
			logit (factor+' matched above threshold')
			if gaugethings[factor]['good'] == 'up':
				direction = 'down'
			else:
				direction = 'up'
			gauge += 1
			logit ('Gauge is now '+str(gauge)+' - '+factor+' '+direction+'.\n')
			gaugefactor.append(factor+' '+direction+', ')
		else:
			logit (factor+' did not affect gauge.\n')
	except TypeError:
		logit ("Null value for ",change)

daysget = 9 # sets how many days of data to get (starting from today)

# Check for and update the gsheet for yesterday's data if not there
if platform == 'linux':
	if checkfile ('dates.txt',fyesterday) == False:
		getcoviddata ('Vaccinedata',daysget,yesterday)
		getcoviddata ('Casedata',daysget,yesterday)
		if resultstotal == daysget *2:
			gsheetupdate(yesterday)
			f = open('dates.txt','a')
			f.write('\n'+fyesterday)
			f.close()

# Run the function to get coviddata for vaccines and cases.

## First we check the dates file to see if the script was already run and email sent so we don't send multiple emails. 
if checkfile ('dates.txt',formattedToday) == False:
	getcoviddata ('Vaccinedata',daysget,getdate)
	getcoviddata ('Casedata',daysget,getdate)
else:
	print ('Email already sent; did not check for data')
	logit ('Email already sent; did not check for data')

if len(coviddataset['Number of patients hospitalized with COVID-19']) < daysget:
	print ("incomplete data")
	logit ("Incomplete Data for Today")
	logit ("Script Complete",'yes')
	exit()
	
# Add the combined Hospitalization + ICU dataset to the dataset. 
Hospicuadd = 0
coviddataset.update({'People in Hospital + ICU':[]})
while Hospicuadd < daysget:
	coviddataset['People in Hospital + ICU'].append(coviddataset['Number of patients hospitalized with COVID-19'][Hospicuadd]+coviddataset['Number of patients in ICU due to COVID-19'][Hospicuadd])
	Hospicuadd += 1

tweet = ''

def adddata (string, kind, posttweet="nopost"):
	push = string
	if kind == 'bullet':
		mdstrt = '-'
		htmlstart = '<li>'
		htmlend = '</li>'
	elif kind == 'heading':
		mdstrt = '#'
		htmlstart = '<h1>'
		htmlend = '</h1>'
	elif kind == 'whitespace':
		mdstrt = ''
		htmlstart = '<br>'
		htmlend = ''
	elif kind == 'p':
		mdstrt = ''
		htmlstart = '<p>'
		htmlend = '</p>'
	print (mdstrt,push)
	global emailbody
	emailbody = emailbody + htmlstart + push + htmlend
	global tweet
	if posttweet == "posttweet":
		tweet = tweet + push + '\n'

# Functions for various reusable calculations. 

## Used to compare the seven day average of changes to a given datum
def sevavcalc(startday,datum):
	if startday == 'today':
		x = 0
		y = 7
	else: 
		x = 1
		y = 8
	sevendays = [] 
	while x < y:
		sevendays.append(int(datum[x]) - int(datum[x+1]))
		x += 1
	return (sum(sevendays) / 7)

# Give it a number, it will give you an emoji arrow based on positive, negative or 0
def arrowcheck(num):
	if num == 0:
		return '↕️'
	elif num < 0:
		return '⬇️'
	else:
		return '⬆️'

# Gets the average of 7 numbers for a given datum
def total_sevavcalc(startday,datum):
	if startday == 'today':
		x = 0
		y = 7
	else: 
		x = 1
		y = 8
	sevendays = [] 
	while x < y:
		sevendays.append(int(coviddataset[datum][x]))
		x += 1
	average = sum(sevendays) / 7
	return int(average)

# Gets the % change of the 7 day average for a datum vs. yesterday's
def total_sevavcalc_change(datum):
	try:
		avdiff = int(total_sevavcalc('today',datum)) / int(total_sevavcalc('yesterday',datum)) - 1
		return avdiff
	except TypeError:
		return "N\A"

def sevaveragegauger(datum):
	return sevavcalc('today',coviddataset[datum]) / sevavcalc('yesterday',coviddataset[datum]) -1

def averagechange_and_add(datum, display):
	sevdayratechange = sevavcalc('today',coviddataset[datum]) / sevavcalc('yesterday',coviddataset[datum]) -1
	if sevdayratechange == 0:
		arrow = '↕️'
	elif sevdayratechange > 0:
		arrow = '⬆️'
	else: 
		arrow = '⬇️' 
	adddata (display+str(round(sevavcalc('today',coviddataset[datum])))+' ('+arrow+' '+str(format(abs(sevdayratechange),".1%"))+')','bullet','posttweet')

def totalaveragesadd(datum,display):
	try:
		adddata (display+
		str(total_sevavcalc('today',datum)) +
		' (' + 
		arrowcheck (total_sevavcalc_change(datum)) +
		' ' +
		str(format(abs(total_sevavcalc_change(datum)),".1%")) + 
		')',
		'bullet')
	except TypeError:
		adddata (display+"N\A",'bullet')		

def NoneCheck (datum):
	if datum == None:
		return "N\A"
	else: return datum

def ratechange (datum):
	try:
		global gauge
		change = round(coviddataset[datum][0] - coviddataset[datum][1])
		ratechange = (coviddataset[datum][0] / coviddataset[datum][1])-1
		if ratechange <= 0:
			arrow = '⬇️'
			color = 'green\">'
		else:
			arrow = '⬆️'
			color = 'red\">'
		gaugeit(ratechange,datum)
		return ("("+arrow+" "+str(format(abs(ratechange),".1%"))+')')
	except TypeError:
		return "N/A"

# This part of the script takes the data, does some calculations, and returns the results.
if checkfile ('dates.txt',formattedToday) == False:
	if resultstotal == daysget *2:
		#----------- Format data, print it, log it to gsheet and send email -----------  
		##----------- Case Data -----------  
		adddata ('🦠 Case Data','heading')
		newcasestoday = coviddataset['Total Cases'][0] - coviddataset['Total Cases'][1] 
		newcasesyesterday = coviddataset['Total Cases'][1] - coviddataset['Total Cases'][2]
		newcaseratechange = (newcasestoday / newcasesyesterday) - 1
		if newcaseratechange == 0:
			arrow = '↕️'
		elif newcaseratechange < 0:
			arrow = '⬇️'
		else:
			arrow = '⬆️'
		gaugeit(newcaseratechange,'New Cases')
		adddata ('New Cases: '+str(round(newcasestoday))+' ('+arrow+' '+str(format(abs(newcaseratechange),".1%"))+')','bullet','posttweet') 
		### Calculate and display 7 day average 
		averagechange_and_add('Total Cases','New Case 7 Day Average: ')
		gaugeit(sevaveragegauger('Total Cases'),'7 Day New Case Average')
		
		# ----------- Hospitalization Data -----------   
		adddata('🏥 Hospitalizations + ICU','heading')
# 		adddata ('Number of patients in hospital: '+
# 			str(NoneCheck(coviddataset['Number of patients hospitalized with COVID-19'][0]))+
# 			str(ratechange('Number of patients hospitalized with COVID-19')),
# 			'bullet',
# 			'posttweet')
# 		totalaveragesadd ('Number of patients hospitalized with COVID-19','7 Day Number in Hospital Average: ')
# 		gaugeit(total_sevavcalc_change('Number of patients hospitalized with COVID-19'),'7 Day Hopsital Average')
		
		# ----------- ICU Data -----------   
# 		adddata ('Number of patients in ICU: '+
# 			str(NoneCheck(coviddataset['Number of patients in ICU due to COVID-19'][0]))+
# 			str(ratechange('Number of patients in ICU due to COVID-19')),
# 			'bullet',
# 			'posttweet')
# 		totalaveragesadd ('Number of patients in ICU due to COVID-19','7 Day Number in ICU Average: ')
# 		gaugeit(total_sevavcalc_change('Number of patients in ICU due to COVID-19'),'7 Day ICU Average')
		
		# --- Hospitalizations + ICU Combined -----
		adddata ('Number of patients in Hospital + ICU: '+
			str(NoneCheck(coviddataset['People in Hospital + ICU'][0]))+
			str(ratechange('People in Hospital + ICU')),
			'bullet',
			'posttweet')
		totalaveragesadd ('People in Hospital + ICU','7 Day Number in Hospital + ICU Average: ')
		gaugeit(total_sevavcalc_change('People in Hospital + ICU'),'People in Hospital + ICU')
		
		# ----------- Vaccine Data -----------  
		adddata ('💉 Vaccination Data','heading')
		ontariopop = 14755211
		
		## 1 Dose
		def vaxchange (datum):
			vaccinepercent = (int(coviddataset[datum][0]) - int(coviddataset['total individuals fully vaccinated'][0])) / ontariopop
			vaccinerate = (int(coviddataset[datum][0]) / int(coviddataset[datum][1])) - 1
			if vaccinerate == 0:
				arrow = '↕️'
			elif vaccinerate < 0:
				arrow = '⬇️'
			else:
				arrow = '⬆️'
			return (str(format(vaccinepercent,".1%"))+' ('+arrow+" "+str(format(abs(vaccinerate),".1%"))+')')
		adddata ('% of People With at Least One Dose: '+str(vaxchange('total doses administered')),'bullet')
		
		## Maxxinated 
		vaccinepercent = (int(coviddataset['total individuals fully vaccinated'][0])) / ontariopop
		vaccinerate = (int(coviddataset['total individuals fully vaccinated'][0]) / int(coviddataset['total individuals fully vaccinated'][1])) - 1
		if vaccinerate == 0:
				arrow = '↕️'
		elif vaccinerate < 0:
			arrow = '⬇️'
		else:
			arrow = '⬆️'
		gaugeit(vaccinerate,'Maxxinated')
		adddata ('% of People Maxxinated: '+str(format(vaccinepercent,".1%"))+' ('+arrow+' '+str(format(abs(vaccinerate),".1%"))+')','bullet','posttweet')
		
		## 3 Shotters 

		vaccinepercent = (int(coviddataset['total individuals 3doses'][0])) / ontariopop
		vaccinerate = (int(coviddataset['total individuals 3doses'][0]) / int(coviddataset['total individuals 3doses'][1])) - 1
		gaugeit(vaccinerate,'3 Shotters')
		if vaccinerate == 0:
				arrow = '↕️'
		elif vaccinerate < 0:
			arrow = '⬇️'
		else:
			arrow = '⬆️'
		adddata ('% of People with 3 Shots: '+str(format(vaccinepercent,".1%"))+' ('+arrow+' '+str(format(abs(vaccinerate),".1%"))+')','bullet','posttweet')
		
		## Doses
		sevdayratechange = sevavcalc('today',coviddataset['total doses administered']) / sevavcalc('yesterday',coviddataset['total doses administered']) -1
		if sevdayratechange > 0:
			arrow = '⬆️'
		else:
			arrow = '⬇️'
		sevdaydoseav = f"{sevavcalc('today',coviddataset['total doses administered']):,.0f}"
		adddata ('7 Day Average Doses Administered: '+ sevdaydoseav +' ('+arrow+' '+str(format(abs(sevdayratechange),".1%"))+')','bullet')
		gaugeit(sevaveragegauger('total doses administered'),'7 Day Dose Average')

		# Finalize the emoji (gauge)
		adddata ('Overall, how are things going right now?','heading')
		if gauge > 6:
			gauge = 6
			logit ('Gauge is now '+str(gauge)+'(Gauge was too high)')
		if gauge < 0:
			gauge = 0
			logit ('Gauge is now '+str(gauge)+'(Gauge was too Low)')
		
		factors = ''
		if gaugefactor == '':
			factors = 'None.'
		else:
			for i in gaugefactor:
				factors += i
			factors = factors[0:len(factors)-2]
		
		adddata (howrthings[str(gauge)],'heading')
		if factors == "":
			factors = "None"
		adddata ('(Emoji Factors: '+factors+'.)','p')
		esubject = esubject + ': ' + howrthings[str(gauge)]
		emoji = howrthings[str(gauge)]
		emailbody = emailbody + '<h2>📈Charts</h2><h3>Cases, Hospitalizations, Vaccines</h3><img src="https://docs.google.com/spreadsheets/d/e/2PACX-1vQgPFb9qYvFkx2QxDN5ympVrqdMvPAsmVsDdhqwMD2ZTTVI9dNNRO06Kxal2j3ruBLDUj5gg_oW2lw3/pubchart?oid=121353037&format=image" alt="Historical Chart"><h3>Vaccine 7-Day Average Dose Rate</h3><img src="https://docs.google.com/spreadsheets/d/e/2PACX-1vQgPFb9qYvFkx2QxDN5ympVrqdMvPAsmVsDdhqwMD2ZTTVI9dNNRO06Kxal2j3ruBLDUj5gg_oW2lw3/pubchart?oid=1049777004&amp;format=image" alt="Vaccine 7 day average history"></p>'
	
		# Send results to the gsheet and send email unless already done

		if platform == 'linux':
			if checkfile ('dates.txt',formattedToday) == False:
				# Update gsheet
				gsheetupdate(getdate)
				logit ('Today\'s gsheet updated')
				# Send email
				url = "https://api.buttondown.email/v1/emails"
				payload = {
					"body": emailbody,
					"subject": esubject
					}
				headers = {
					"Authorization": f"TOKEN {BDToken}"
					}
				res = requests.post(url, data=payload, headers=headers)
				logit ("Email sent with complete data.\n")
				f = open('dates.txt','a')
				f.write('\n'+formattedToday)
				f.close()
				# Post Tweet
				tweet = "Tom's Ontario Covid Report For "+str(getdate.strftime('%B %d, %Y'))+"("+emoji+")"+"\n"+tweet
				url = "https://hooks.zapier.com/hooks/catch/252299/b497mkf"
				payload = {"tweet":tweet}
				headers = {}
				res = requests.post(url, data=payload, headers=headers)
				logit ("Posted Tweet\n")
			else:
				logit ("Complete data, but email already sent.\n")
				headers = {}
				res = requests.post(url, data=payload, headers=headers)
		else:
			logit ("Complete data, but not running in production, so no email sent.\n")
	else:
		print ('Incomplete data for today!\n')
		logit ("Incomplete data for today!")


# 	coviddataset = {
# 	  'Total Cases': [],
# 	  'Number of patients hospitalized with COVID-19': [],
# 	  'Number of patients in ICU due to COVID-19': [],
# 	  'total doses administered': [],
# 	  'total individuals fully vaccinated': [],
# 	}
# 	getcoviddata ('Vaccinedata',daysget,getdate)
# 	getcoviddata ('Casedata',daysget,getdate)
# 	for i in coviddataset:
# 		print ('- ',i,":",coviddataset[i])

# This prints the reported date if yesterday was asked for.
if reporteddate != '':
	print (reporteddate)

logit ("Script Complete"+cron+'\n'+'-----------------','yes')

# Show script runtime - uncomment for troubleshooting 

#print ('\nTimet to run: ',datetime.now() - scriptstart)