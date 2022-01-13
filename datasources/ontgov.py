#!/usr/bin/env python3

from datetime import datetime, timedelta, date
import json
import csv
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

    def __init__(self):
        self.map = {}

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

    def _cleanup(self, og_results):
        if not og_results["success"]:
            raise Exception("Failed to pull data from OntarioGov")
        results = og_results["result"]["records"][0]
        results.update((k, int(v)) for k, v in results.items())
        return results

    def vaccinedata(self, date: datetime):
        return self._cleanup(
            self.query(
                date, "VaccineData", OntarioGov.DATASOURCES["VaccineData"]["fields"]
            )
        )

    def casedata(self, date: datetime):
        return self._cleanup(
            self.query(date, "CaseData", OntarioGov.DATASOURCES["CaseData"]["fields"])
        )

    def get(self, date: datetime):
        self.map[str(date)] = self.vaccinedata(date)
        self.map[str(date)].update(self.casedata(date))
        self.map[str(date)].update({"date": str(date)})
        return self.map[str(date)]


class CovidRecords(OntarioGov):
    FIELDNAMES = [
        "date",
        "total_doses_administered",
        "total_individuals_at_least_one",
        "total_individuals_fully_vaccinated",
        "total_individuals_3doses",
        "Total Cases",
        "Number of patients hospitalized with COVID-19",
        "Number of patients in ICU due to COVID-19",
    ]

    def __init__(self, filename="foo.csv"):
        super().__init__()
        self.filename = filename
        try:
            with open(filename, newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    date = row["date"]
                    self.map[date] = row
        except FileNotFoundError:
            self.map = {}

    def get(self, date: datetime):
        if str(date) not in self.map:
            return super().get(date)
        return self.map[str(date)]

    def write(self):
        with open(self.filename, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, CovidRecords.FIELDNAMES)
            writer.writeheader()
            for d in sorted(self.map.keys(), reverse=True):
                writer.writerow(self.map[d])

    def backfill(self, n=10):
        [records.get(date) for date in DateRanges.range(n)]


if __name__ == "__main__":
    records = CovidRecords()
    records.backfill()
    records.write()
