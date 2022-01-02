# Import Modules
import pandas as pd
from datetime import date
import csv
from csv import DictWriter
from csv import DictReader
import time
import json
import urllib.request as ur
import urllib.parse as prs
from datetime import datetime, timedelta

###---Global Variables----
# Sets the name of the CSV file we'll be using to store data 
file = 'ontario_covid_data.csv'

# Creating the datasourceinfo variable which stores information about how to query different datasets 
datasources = {
'CaseData': {
	'id': 'ed270bb8-340b-41f9-a7c6-e8ef587e6d11',
	'datename': 'Reported Date',
	'fields': [
		'Total Cases',
		'Number of patients hospitalized with COVID-19',
		'Number of patients in ICU due to COVID-19'
		]
	},
'VaccineData': {
	'id': '8a89caa9-511c-4568-af89-7f2174b4378c',
	'datename': 'report_date',
	'fields': [
		'total_doses_administered',
		'total_individuals_at_least_one',
		'total_individuals_fully_vaccinated',
		'total_individuals_3doses'
		]
	}
}

###---Functions---
# get list of fields from CSV file
def OpenCSV():
	global localData
	global field_names
	with open(file) as csv_file:
		csv_reader = csv.DictReader(csv_file)
		dict_from_csv = dict(list(csv_reader)[0])
		field_names = list(dict_from_csv.keys())
	localData = pd.read_csv(file)
	## Set the index of the CSV file to 'date' so we can reference rows by dates
	localData.set_index('date', inplace=True)
	localData.head()

# Function to pass in a new row to the CSV file 
def addRow(elements):
	# Open file in append mode
	with open(file, 'a+', newline='') as write_obj:
		# Create a writer object from csv module
		dict_writer = DictWriter(write_obj, fieldnames=field_names)
		# Add dictionary as row in the csv
		dict_writer.writerow(elements)

# Function to add given data to a given row and column 
def addValue(row,column,value):
	localData.loc[row,column] = value
	localData.to_csv(file)

# Function to add a given date as a new row to the CSV 
def dateCheck(day):
	try:
		localData.loc[day]
		return 'Date found'
	except KeyError:
		return 'Date not found'

# Function to check blank fields for a given date 
def blankchecker(date,dataset):
	fieldquery = []
	for i in datasources[dataset]['fields']:
		try:
			checker = 1 + int(localData.loc[date,i])
		except ValueError:
			fieldquery.append(i)
	if fieldquery:
		return fieldquery

# Function to build a query and get data
def querier(dataset,qfields,qdate):
	urlstart = 'https://data.ontario.ca/api/3/action/datastore_search?'
	resourceid = 'resource_id=' + datasources[dataset]['id']
	fieldQuery = 'fields='
	numfields = len(qfields)
	for x in qfields:
		comma = '' if numfields == 1 else ','
		fieldQuery = fieldQuery+'\"'+x+'\"' + comma
		numfields -= 1
	reqdate = 'filters={\"' + datasources[dataset]['datename'] + '\":[\"' + qdate + '\"]}'
	queryurl = urlstart + resourceid + '&' + fieldQuery + '&' + reqdate
	queryurl = queryurl.replace(' ', '%20')
	fileobj = ur.urlopen(queryurl)
	return json.loads(fileobj.read())

# Stub of a function to get blank data. Need to run this in a loop for every blank cell in each dataset for each day...
def blankfiller(date,dataset):
	qfields = blankchecker(date,dataset)
	if qfields != None:
		reqdata = querier(dataset,qfields,date)
		if reqdata['result']['total'] > 0:
			for i in qfields:
				addValue(date, i, reqdata['result']['records'][0][i])
				OpenCSV()

if __name__ == '__main__':
    import argparse
    import os
    parser = argparse.ArgumentParser()
    parser.add_argument("--csvdir", help="Directory of csv file")
    args = parser.parse_args()
    if(args.csvdir):
        file = os.path.join(args.csvdir, file)
    # Open the CSV
    OpenCSV()
    
    # Check if there are any missing rows and create if not
    today = date.today()
    ftoday = str(today)
    datesback = 10
    
    # Populate any missing dates
    checkdate = today
    datesbeckcheck = datesback
    while datesbeckcheck >0:
    	OpenCSV()
    	if dateCheck(str(checkdate)) == 'Date not found':
    		addRow({'date': checkdate})
    	checkdate = checkdate - timedelta(days=1)
    	datesbeckcheck -= 1
    
    # Populate missing values 
    datesbackvalues = datesback
    checkdate = today
    while datesbackvalues > 0:
    	for i in datasources:
    		OpenCSV()
    		blankfiller (str(checkdate),i)
    	checkdate = checkdate - timedelta(days=1)
    	datesbackvalues -= 1
    	
    OpenCSV()
    
    localData.sort_values(['date'], 
                        axis=0,
                        ascending=[False], 
                        inplace=True)
    localData.to_csv(file)
