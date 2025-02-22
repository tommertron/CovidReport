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
import os

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)


# Create logging function
## This function logs messages that are passed to it to a log file, along with a timestamp that the message was sent.
def logit(event, dtime="no"):
    now = datetime.now()
    if dtime == "yes":
        logDateTime = now.strftime("%m/%d/%y - %H:%M:%S.%f")[:-5]
        dash = " - "
    else:
        logDateTime = ""
        dash = "- "
    f = open("log.txt", "a")
    f.write("\n" + logDateTime + dash + event)
    f.close()


# This section sets some variables based on arguments that were passed in when called from the command line.
## This variable records whether the script was called via cron job or not.
cron = ""

# Log that the job is starting.
logit("Starting script\n" + cron, "yes")

## Define some dates!
reporteddate = ""
getdate = (
    date.today()
)  # + timedelta(days=+1) #Uncomment the right section to point to tomorrow's date. To test instances where today's data is not available.
formattedToday = str(getdate.strftime("%m/%d"))
yesterday = getdate - timedelta(days=1)
fyesterday = str(yesterday.strftime("%m/%d"))
reportingdate = getdate.strftime(
    "%B %d, %Y"
)  # This is used to display the date the report was run


# This is a function to check a given file for a given term to see if it's there.
def checkfile(file_name, string_to_search):
    with open(file_name, "r") as read_obj:
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
        if sys.argv[argslot] == "yesterday":
            getdate = date.today() - timedelta(days=1)
            reporteddate = "**Yesterday's Data**", getdate
        elif sys.argv[argslot] == "cron":
            cron = "(CRON)"
        argslot += 1


# Web Tokens
## This function gets a token from a given web service for authentication. This allows the tokens to be stored in a file separate from the script for security purposes.
def keygetter(file):
    f = open(file, "r")
    return f.read()


## This is the token for the Buttondown service used for sending the newsletter.
BDToken = keygetter("BDToken.txt")
## This is the token for If This then That, which updates the Google sheet.
IFToken = keygetter("IFToken.txt")


# This function updates the Google Sheet with a given set of data (via IFTTT)
def gsheetupdate(date):
    hookurl = "https://maker.ifttt.com/trigger/addsheet/with/key/" + IFToken
    payload = {
        "value1": str(coviddataset["total_doses_administered"][0])
        + "|"
        + str(coviddataset["total_individuals_fully_vaccinated"][0]),
        "value2": str(coviddataset["Total Cases"][0])
        + "|"
        + str(coviddataset["Number of patients hospitalized with COVID-19"][0]),
        "value3": str(coviddataset["Number of patients in ICU due to COVID-19"][0])
        + "|"
        + str(date)
        + "|"
        + str(coviddataset["total_individuals_at_least_one"][0]),
    }
    headers = {}
    res = requests.post(hookurl, data=payload, headers=headers)


# Email Stuff
## Section for setting variables that will be used for the newsletter.
htmlstart = '<span style="color:'
htmlend = "</span>"
esubject = "Tom's Ontario COVID Report for " + str(getdate.strftime("%B %d, %Y"))
emailbody = ""

# Define Query Parameters

## URL Query Variables - Universal
### These are the variables we will use to build our query.
urlstart = "https://data.ontario.ca/api/3/action/datastore_search?"
today = str(date.today()) + "T00:00:00"
urlfilter = ""
fieldQuery = ""
resourceid = ""
friendlyname = ""

## URL Query Variables - Per Dataset
### Each Ontario dataset has a unique resource ID that we use to identify it when querying.
resourceidlist = {
    "Vaccinedata": "8a89caa9-511c-4568-af89-7f2174b4378c",
    "Casedata": "ed270bb8-340b-41f9-a7c6-e8ef587e6d11",
}
### For some reason, each Ontario dataset seems to have a different field name for reported data. This specifies the correct date field name per dataset so we can query by date.
datefieldlist = {"Vaccinedata": "report_date", "Casedata": "Reported Date"}
### This variable stores all of the fields we want to retrieve from each Ontario dataset. The script will get and print all of today's data for each field listed here.
fieldlist = {
    "Vaccinedata": [
        "total_doses_administered",
        "total_individuals_at_least_one",
        "total_individuals_fully_vaccinated",
        "total_individuals_3doses",
        "report_date",
    ],
    "Casedata": [
        "Total Cases",
        "Number of patients hospitalized with COVID-19",
        "Number of patients in ICU due to COVID-19",
        "Reported Date",
    ],
}
## This specifies what we want to call each dataset when we output its results.
friendlynamelist = {"Vaccinedata": "Vaccine Data", "Casedata": "Case Data"}

## Create a dictionary variable that will store the all the data that we retrieve
coviddataset = {}
## This little loop takes all of the fields we listed in 'field list' and adds them to the coviddataset dictionary variable as keys. We'l use this later to parse through and add values to.
for x in fieldlist:
    for i in fieldlist[x]:
        coviddataset[i] = []

## This variable will store the number of results we get to check if they are complete. It starts at 0.
resultstotal = 0

# Get Data Section


## This is the big complicated function that we will call to get the different datasets later. We pass in the dataset, how many dates we are getting, and the reporting date (today or another day).
def getcoviddata(dataset, getdays, fetchdate):
    # Get dataset specific values for the query
    resourceid = resourceidlist[dataset]
    friendlyname = friendlynamelist[dataset]
    fields = fieldlist[dataset]
    urlfilter = '"' + datefieldlist[dataset] + '":' + "["
    expectedresults = getdays
    # getdays = getdays + 1
    while getdays > 0:
        urlfilter = urlfilter + '"' + str(fetchdate) + '"'
        fetchdate = fetchdate - timedelta(days=1)
        getdays = getdays - 1
        if getdays > 0:
            urlfilter = urlfilter + ","
    urlfilter = urlfilter + "]"
    urlfilter = urlfilter.replace(" ", "%20")
    fieldQuery = ""
    # Set global variables
    global resultstotal
    global coviddataset
    fields = fieldlist[dataset]
    ## Create field list query section
    for x in fields[:-1]:
        fieldQuery = fieldQuery + "'" + x + "',"
    fieldQuery = fieldQuery + "'" + fields[len(fields) - 1] + "'"
    fieldQuery = fieldQuery.replace(" ", "%20")
    fieldQuery = fieldQuery.replace("'", '"')
    # Make url
    queryurl = (
        urlstart
        + "resource_id="
        + resourceid
        + "&fields="
        + fieldQuery
        + "&filters={"
        + urlfilter
        + "}"
        + '&sort="'
        + datefieldlist[dataset]
        + '"'
    )
    queryurl = queryurl.replace(" ", "%20")
    logit(dataset + " url: " + queryurl)
    # print ('** ' + friendlynamelist[dataset] + ' Report *')
    url = queryurl
    fileobj = ur.urlopen(url)
    ## Format Data Into Json
    gotdata = fileobj.read()
    nicedata = json.loads(gotdata)
    resultstotal = resultstotal + nicedata["result"]["total"]
    resultscheck = nicedata["result"]["total"]
    if resultscheck > 0:
        quay = resultscheck - 1
        while quay > 0 - 1:
            for i in nicedata["result"]["records"][quay]:
                recname = i
                recnum = nicedata["result"]["records"][quay][i]
                if type(recnum) == str:
                    recnum = recnum.replace(",", "")
                # Add result to global dataset
                coviddataset[recname].append(recnum)
            quay = quay - 1


daysget = 9  # sets how many days of data to get (starting from today)

# Check for and update the gsheet for yesterday's data if not there
if platform == "linux":
    if checkfile("dates.txt", fyesterday) is False:
        getcoviddata("Vaccinedata", daysget, yesterday)
        getcoviddata("Casedata", daysget, yesterday)
        if resultstotal == daysget * 2:
            gsheetupdate(yesterday)
            f = open("dates.txt", "a")
            f.write("\n" + fyesterday)
            f.close()

# Run the function to get coviddata for vaccines and cases.

## First we check the dates file to see if the script was already run and email sent so we don't send multiple emails.

if checkfile("dates.txt", formattedToday) is False:
    getcoviddata("Vaccinedata", daysget, getdate)
    getcoviddata("Casedata", daysget, getdate)
else:
    print("Email already sent; did not check for data")
    logit("Email already sent; did not check for data")

if len(coviddataset["Number of patients hospitalized with COVID-19"]) < daysget:
    print("incomplete data")
    logit("Incomplete Data for Today")
    logit("Script Complete", "yes")
    exit()

# Add the combined Hospitalization + ICU dataset to the dataset.
Hospicuadd = 0
coviddataset.update({"People in Hospital + ICU": []})
while Hospicuadd < daysget:
    coviddataset["People in Hospital + ICU"].append(
        coviddataset["Number of patients hospitalized with COVID-19"][Hospicuadd]
        + coviddataset["Number of patients in ICU due to COVID-19"][Hospicuadd]
    )
    Hospicuadd += 1

tweet = ""


def adddata(string, kind, posttweet="nopost"):
    push = string
    if kind == "bullet":
        mdstrt = "-"
        htmlstart = "<li>"
        htmlend = "</li>"
    elif kind == "heading":
        mdstrt = "#"
        htmlstart = "<h1>"
        htmlend = "</h1>"
    elif kind == "whitespace":
        mdstrt = ""
        htmlstart = "<br>"
        htmlend = ""
    elif kind == "p":
        mdstrt = ""
        htmlstart = "<p>"
        htmlend = "</p>"
    print(mdstrt, push)
    global emailbody
    emailbody = emailbody + htmlstart + push + htmlend
    global tweet
    if posttweet == "posttweet":
        tweet = tweet + push + "\n"


# Functions for various reusable calculations.

## Used to compare the seven day average of changes to a given datum
def sevavcalc(startday, datum):
    if startday == "today":
        x = 0
        y = 7
    else:
        x = 1
        y = 8
    sevendays = []
    while x < y:
        sevendays.append(int(datum[x]) - int(datum[x + 1]))
        x += 1
    return sum(sevendays) / 7


# Give it a number, it will give you an emoji arrow based on positive, negative or 0
def arrowcheck(num):
    if num == 0:
        return "↕️"
    elif num < 0:
        return "⬇️"
    else:
        return "⬆️"


# Gets the average of 7 numbers for a given datum
def total_sevavcalc(startday, datum):
    if startday == "today":
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
        avdiff = (
            int(total_sevavcalc("today", datum))
            / int(total_sevavcalc("yesterday", datum))
            - 1
        )
        return avdiff
    except TypeError:
        return "N\A"


def sevaveragegauger(datum):
    return (
        sevavcalc("today", coviddataset[datum])
        / sevavcalc("yesterday", coviddataset[datum])
        - 1
    )


def averagechange_and_add(datum, display):
    sevdayratechange = (
        sevavcalc("today", coviddataset[datum])
        / sevavcalc("yesterday", coviddataset[datum])
        - 1
    )
    if sevdayratechange == 0:
        arrow = "↕️"
    elif sevdayratechange > 0:
        arrow = "⬆️"
    else:
        arrow = "⬇️"

    number = sevavcalc("today", coviddataset[datum])
    adddata(
        display
        + f"{number:,.0f}"
        + " ("
        + arrow
        + " "
        + str(format(abs(sevdayratechange), ".1%"))
        + ")",
        "bullet",
        "posttweet",
    )


def totalaveragesadd(datum, display):
    try:
        adddata(
            display
            + str(total_sevavcalc("today", datum))
            + " ("
            + arrowcheck(total_sevavcalc_change(datum))
            + " "
            + str(format(abs(total_sevavcalc_change(datum)), ".1%"))
            + ")",
            "bullet",
        )
    except TypeError:
        adddata(display + "N\A", "bullet")


def NoneCheck(datum):

    if datum is None:

        return "N\A"
    else:
        return datum


def ratechange(datum):
    try:
        change = round(coviddataset[datum][0] - coviddataset[datum][1])
        ratechange = (coviddataset[datum][0] / coviddataset[datum][1]) - 1
        if ratechange <= 0:
            arrow = "⬇️"
            color = 'green">'
        else:
            arrow = "⬆️"
            color = 'red">'
        return "(" + arrow + " " + str(format(abs(ratechange), ".1%")) + ")"
    except TypeError:
        return "N/A"


# This part of the script takes the data, does some calculations, and returns the results.

if checkfile("dates.txt", formattedToday) is False:
    if resultstotal == daysget * 2:
        # ----------- Format data, print it, log it to gsheet and send email -----------

        # ----------- Hospitalization Data -----------
        adddata("🏥 Hospitalizations + ICU", "heading")
        adddata(
            "Number of patients in hospital: "
            + str(
                NoneCheck(
                    coviddataset["Number of patients hospitalized with COVID-19"][0]
                )
            )
            + str(ratechange("Number of patients hospitalized with COVID-19")),
            "bullet",
            "posttweet",
        )
        totalaveragesadd(
            "Number of patients hospitalized with COVID-19",
            "7 Day Number in Hospital Average: ",
        )
        # ----------- ICU Data -----------
        adddata(
            "Number of patients in ICU: "
            + str(
                NoneCheck(coviddataset["Number of patients in ICU due to COVID-19"][0])
            )
            + str(ratechange("Number of patients in ICU due to COVID-19")),
            "bullet",
            "posttweet",
        )
        totalaveragesadd(
            "Number of patients in ICU due to COVID-19", "7 Day Number in ICU Average: "
        )

        # ----------- Vaccine Data -----------
        adddata("💉 Vaccination Data", "heading")
        ontariopop = 14755211

        ## 1 Dose
        vaccinepercent = (
            int(coviddataset["total_individuals_at_least_one"][0])
        ) / ontariopop
        vaccinerate = (
            int(coviddataset["total_individuals_at_least_one"][0])
            / int(coviddataset["total_individuals_at_least_one"][1])
        ) - 1
        if vaccinerate == 0:
            arrow = "↕️"
        elif vaccinerate < 0:
            arrow = "⬇️"
        else:
            arrow = "⬆️"
        adddata(
            "% of People With at Least One Dose: "
            + str(format(vaccinepercent, ".1%"))
            + " ("
            + arrow
            + " "
            + str(format(abs(vaccinerate), ".1%"))
            + ")",
            "bullet",
            "posttweet",
        )

        ## Maxxinated
        vaccinepercent = (
            int(coviddataset["total_individuals_fully_vaccinated"][0])
        ) / ontariopop
        vaccinerate = (
            int(coviddataset["total_individuals_fully_vaccinated"][0])
            / int(coviddataset["total_individuals_fully_vaccinated"][1])
        ) - 1
        if vaccinerate == 0:
            arrow = "↕️"
        elif vaccinerate < 0:
            arrow = "⬇️"
        else:
            arrow = "⬆️"
        adddata(
            "% of People Maxxinated: "
            + str(format(vaccinepercent, ".1%"))
            + " ("
            + arrow
            + " "
            + str(format(abs(vaccinerate), ".1%"))
            + ")",
            "bullet",
            "posttweet",
        )

        ## 3 Shotters
        vaccinepercent = (int(coviddataset["total_individuals_3doses"][0])) / ontariopop
        vaccinerate = (
            int(coviddataset["total_individuals_3doses"][0])
            / int(coviddataset["total_individuals_3doses"][1])
        ) - 1
        if vaccinerate == 0:
            arrow = "↕️"
        elif vaccinerate < 0:
            arrow = "⬇️"
        else:
            arrow = "⬆️"
        adddata(
            "% of People with 3 Shots: "
            + str(format(vaccinepercent, ".1%"))
            + " ("
            + arrow
            + " "
            + str(format(abs(vaccinerate), ".1%"))
            + ")",
            "bullet",
            "posttweet",
        )

        ## Doses
        sevdayratechange = (
            sevavcalc("today", coviddataset["total_doses_administered"])
            / sevavcalc("yesterday", coviddataset["total_doses_administered"])
            - 1
        )
        if sevdayratechange > 0:
            arrow = "⬆️"
        else:
            arrow = "⬇️"
        sevdaydoseav = (
            f"{sevavcalc('today',coviddataset['total_doses_administered']):,.0f}"
        )
        adddata(
            "7 Day Average Doses Administered: "
            + sevdaydoseav
            + " ("
            + arrow
            + " "
            + str(format(abs(sevdayratechange), ".1%"))
            + ")",
            "bullet",
        )
        ##----------- Case Data -----------
        adddata("🦠 Case Data", "heading")
        newcasestoday = coviddataset["Total Cases"][0] - coviddataset["Total Cases"][1]
        newcasesyesterday = (
            coviddataset["Total Cases"][1] - coviddataset["Total Cases"][2]
        )
        newcaseratechange = (newcasestoday / newcasesyesterday) - 1
        if newcaseratechange == 0:
            arrow = "↕️"
        elif newcaseratechange < 0:
            arrow = "⬇️"
        else:
            arrow = "⬆️"
        adddata(
            "New Cases: "
            + f"{newcasestoday:,.0f}"
            + " ("
            + arrow
            + " "
            + str(format(abs(newcaseratechange), ".1%"))
            + ")",
            "bullet",
            "posttweet",
        )
        ### Calculate and display 7 day average
        averagechange_and_add("Total Cases", "New Case 7 Day Average: ")

        # Add charts to email body
        emailbody = (
            emailbody
            + '<h2>📈Charts</h2><h3><a href="https://docs.google.com/spreadsheets/d/e/2PACX-1vQgPFb9qYvFkx2QxDN5ympVrqdMvPAsmVsDdhqwMD2ZTTVI9dNNRO06Kxal2j3ruBLDUj5gg_oW2lw3/pubchart?oid=121353037&format=interactive">Cases, Hospitalizations, Vaccines</a></h3><img src="https://docs.google.com/spreadsheets/d/e/2PACX-1vQgPFb9qYvFkx2QxDN5ympVrqdMvPAsmVsDdhqwMD2ZTTVI9dNNRO06Kxal2j3ruBLDUj5gg_oW2lw3/pubchart?oid=121353037&format=image" alt="Historical Chart"><h3>Vaccine 7-Day Average Dose Rate</h3><img src="https://docs.google.com/spreadsheets/d/e/2PACX-1vQgPFb9qYvFkx2QxDN5ympVrqdMvPAsmVsDdhqwMD2ZTTVI9dNNRO06Kxal2j3ruBLDUj5gg_oW2lw3/pubchart?oid=1049777004&amp;format=image" alt="Vaccine 7 day average history"></p>'
        )

        # Send results to the gsheet and send email unless already done

        if platform == "linux":
            if checkfile("dates.txt", formattedToday) is False:
                # Update gsheet
                gsheetupdate(getdate)
                logit("Today's gsheet updated")
                # Send email
                url = "https://api.buttondown.email/v1/emails"
                payload = {"body": emailbody, "subject": esubject}
                headers = {"Authorization": f"TOKEN {BDToken}"}
                res = requests.post(url, data=payload, headers=headers)
                logit("Email sent with complete data.\n")
                f = open("dates.txt", "a")
                f.write("\n" + formattedToday)
                f.close()
                # Post Tweet
                tweet = (
                    "Tom's Ontario Covid Report For "
                    + str(getdate.strftime("%B %d, %Y"))
                    + "("
                    + emoji
                    + ")"
                    + "\n"
                    + tweet
                )
                url = "https://hooks.zapier.com/hooks/catch/252299/b497mkf"
                payload = {"tweet": tweet}
                headers = {}
                res = requests.post(url, data=payload, headers=headers)
                logit("Posted Tweet\n")
            else:
                logit("Complete data, but email already sent.\n")
                headers = {}
                res = requests.post(url, data=payload, headers=headers)
        else:
            logit("Complete data, but not running in production, so no email sent.\n")
    else:
        print("Incomplete data for today!\n")
        logit("Incomplete data for today!")

# This prints the reported date if yesterday was asked for.
if reporteddate != "":
    print(reporteddate)

logit("Script Complete" + cron + "\n" + "-----------------", "yes")

# Show script runtime - uncomment for troubleshooting

# print ('\nTimet to run: ',datetime.now() - scriptstart)
