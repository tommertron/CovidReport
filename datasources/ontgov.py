#!/usr/bin/env python3

from datetime import datetime, timedelta, date
import json
import urllib.request as ur
import urllib.parse as prs


class DateRanges:
    """Generate a list of 10 datetime objects starting from today"""

    @staticmethod
    def range(size: int = 10):
        return [DateRanges._daysago(i) for i in range(size)]

    @staticmethod
    def _daysago(days: int) -> datetime:
        return date.today() - timedelta(days=days)


class CovidData:
    def missing(self, date: datetime) -> bool:
        return True


class OntarioGov(CovidData):
    DATASOURCES = {
        "CaseData": {
            "id": "ed270bb8-340b-41f9-a7c6-e8ef587e6d11",
            "datename": "Reported Date",
            "fields": [
                "Total Cases",
                "Number of patients hospitalized with COVID-19",
                "Number of patients in ICU due to COVID-19",
            ],
        },
        "VaccineData": {
            "id": "8a89caa9-511c-4568-af89-7f2174b4378c",
            "datename": "report_date",
            "fields": [
                "total_doses_administered",
                "total_individuals_at_least_one",
                "total_individuals_fully_vaccinated",
                "total_individuals_3doses",
            ],
        },
    }

    def query(self, date: datetime, dataset: str, qfields):
        """Query the ontario govt http endpoint"""
        urlstart = "https://data.ontario.ca/api/3/action/datastore_search?"
        resourceid = "resource_id=" + OntarioGov.DATASOURCES[dataset]["id"]
        fieldQuery = "fields=%s" % (",".join(qfields))
        reqdate = (
            'filters={"'
            + OntarioGov.DATASOURCES[dataset]["datename"]
            + '":["'
            + str(date)
            + '"]}'
        )
        queryurl = urlstart + resourceid + "&" + fieldQuery + "&" + reqdate
        queryurl = queryurl.replace(" ", "%20")
        fileobj = ur.urlopen(queryurl)
        return json.loads(fileobj.read())

    def vaccinedata(self, date: datetime):
        og_results = self.query(
            date, "VaccineData", OntarioGov.DATASOURCES["VaccineData"]["fields"]
        )
        if not og_results["success"]:
            raise Exception("Failed to pull data from OntarioGov")
        results = og_results["result"]["records"][0]
        # convert values to int
        results.update((k, int(v)) for k, v in results.items())
        return results

    def get(self, date: datetime):
        if str(date) not in self.map:
            self.map[str(date)] = self.vaccinedata(date)


class CSV(OntarioGov):
    def __init__(self):
        self.map = {}


if __name__ == "__main__":
    csv = CSV()
    csv.get(date.today())
    print(csv.map)
