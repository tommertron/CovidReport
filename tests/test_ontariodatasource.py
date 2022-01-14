#!/usr/bin/env python3

import unittest
import datetime
import json
from unittest.mock import MagicMock, patch
from datasources import ontgov

expected_results = """{"help": "https://data.ontario.ca/api/3/action/help_show?name=datastore_search", "success": true, "result": {"include_total": true, "resource_id": "8a89caa9-511c-4568-af89-7f2174b4378c", "fields": [{"type": "int", "id": "_id"}, {"info": {"notes": "", "type_override": "timestamp", "label": ""}, "type": "timestamp", "id": "report_date"}, {"info": {"notes": "", "type_override": "numeric", "label": ""}, "type": "numeric", "id": "previous_day_total_doses_administered"}, {"info": {"notes": "", "type_override": "numeric", "label": ""}, "type": "numeric", "id": "previous_day_at_least_one"}, {"info": {"notes": "", "type_override": "numeric", "label": ""}, "type": "numeric", "id": "previous_day_fully_vaccinated"}, {"type": "text", "id": "previous_day_3doses"}, {"info": {"notes": "", "type_override": "numeric", "label": ""}, "type": "numeric", "id": "total_doses_administered"}, {"type": "text", "id": "total_individuals_at_least_one"}, {"type": "text", "id": "total_individuals_partially_vaccinated"}, {"type": "text", "id": "total_doses_in_fully_vaccinated_individuals"}, {"type": "text", "id": "total_individuals_fully_vaccinated"}, {"type": "text", "id": "total_individuals_3doses"}], "records_format": "objects", "records": [{"total_doses_administered": 28853124, "total_individuals_at_least_one": "12307610", "total_individuals_fully_vaccinated": "11493087", "total_individuals_3doses": "5033258"}], "_links": {"start": "/api/3/action/datastore_search?fields=total_doses_administered%2Ctotal_individuals_at_least_one%2Ctotal_individuals_fully_vaccinated%2Ctotal_individuals_3doses&filters=%7B%22report_date%22%3A%5B%222022-01-12%22%5D%7D&resource_id=8a89caa9-511c-4568-af89-7f2174b4378c", "next": "/api/3/action/datastore_search?fields=total_doses_administered%2Ctotal_individuals_at_least_one%2Ctotal_individuals_fully_vaccinated%2Ctotal_individuals_3doses&offset=100&filters=%7B%22report_date%22%3A%5B%222022-01-12%22%5D%7D&resource_id=8a89caa9-511c-4568-af89-7f2174b4378c"}, "filters": {"report_date": ["2022-01-12"]}, "total": 1}}"""


class MockedDate(datetime.date):
    @classmethod
    def today(cls):
        return cls(2022, 1, 12)


datetime.date = MockedDate


class TestOntarioDataSource(unittest.TestCase):
    def test_query_vaccinedata(self):
        with patch.object(
            ontgov.OntarioGov, "query", return_value=json.loads(expected_results)
        ) as mock_method:
            og = ontgov.OntarioGov()
            results = og.vaccinedata(datetime.date.today())
        print(results)
        mock_method.assert_called_with(
            datetime.date(2022, 1, 12),
            "VaccineData",
            [
                "total_doses_administered",
                "total_individuals_at_least_one",
                "total_individuals_fully_vaccinated",
                "total_individuals_3doses",
            ],
        )
        self.assertEqual(results["total_doses_administered"], 28853124)
        self.assertEqual(results["total_individuals_at_least_one"], 12307610)
        self.assertEqual(results["total_individuals_fully_vaccinated"], 11493087)
        self.assertEqual(results["total_individuals_3doses"], 5033258)


class TestDateRanges(unittest.TestCase):
    def test_daterange_ten(self):
        dates = ontgov.DateRanges.range()
        self.assertEqual(len(dates), 10)

    def test_daterange_five(self):
        dates = ontgov.DateRanges.range(5)
        self.assertEqual(len(dates), 5)


if __name__ == "__main__":
    unittest.main()
