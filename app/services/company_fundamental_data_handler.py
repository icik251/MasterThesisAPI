from collections import defaultdict

import requests


class CompanyFundamentalDataHandler:
    def __init__(
        self,
    ) -> None:
        pass

    def process_data(self, list_of_reports_data: list) -> dict:
        dict_of_formatted_data = defaultdict(dict)
        for report_data in list_of_reports_data:
            for k, v in report_data.items():
                if k == "fiscalDateEnding":
                    dict_of_formatted_data[v]
                    curr_fiscal_data = v
                elif k == "reportedCurrency":
                    dict_of_formatted_data[curr_fiscal_data][k] = v
                else:
                    if v == "None":
                        v = None
                    else:
                        v = float(v)
                    dict_of_formatted_data[curr_fiscal_data][k] = v

        return dict_of_formatted_data


# some_obj = CompanyFundamentalDataHanddler()
# r = requests.get("https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol=AE&apikey=DV3U4RGOYLYSQHN8")
# some_obj.process_data(r.json()['quarterlyReports'])
