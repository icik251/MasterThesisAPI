from collections import defaultdict
from datetime import datetime
import traceback
from .fundamental_data_handler import FundamentalDataHandler
import pandas as pd
import json
import requests


class CompanyInputDataHandler:
    def __init__(
        self,
        list_company,
        list_inflation_prices,
        fundamental_data_dict,
        df_filings_deadlines,
    ) -> None:
        self.list_company = list_company
        self.list_inflation_prices = list_inflation_prices
        self.fundamental_data_dict = fundamental_data_dict
        self.df_filings_deadlines = df_filings_deadlines
        self.list_of_input_company = []

        self.k_folds = [1, 2, 3, 4]
        self.k_fold_rules = {
            2017: {1: "val", 2: "train", 3: "train", 4: "train"},
            2018: {1: "train", 2: "val", 3: "train", 4: "train"},
            2019: {1: "train", 2: "train", 3: "val", 4: "train"},
            2020: {1: "train", 2: "train", 3: "train", 4: "val"},
            2021: {1: "test", 2: "test", 3: "test", 4: "test"},
        }

        # basically if we are 2017, we indicate that for K-FOLD 1, this is used for val
        # for K-FOLD 2, this is used for train, etc.
        # Example for 2017
        # self.k_fold_config_example = {1: "val", 2: "train", 3: "train", 4: "train"}

    def _is_filing_on_time(self, filing_type, quarter, company_type, filing_date):
        # check if company_type was modified
        res_type = company_type.split(";")
        company_type = res_type[1] if len(res_type) > 1 else res_type[0]

        # change to non_accelerated if smaller
        company_type = (
            "non_accelerated_filer"
            if company_type == "smaller_reporting_company"
            else company_type
        )

        filing_date_datetime = datetime.fromisoformat(str(filing_date))
        try:
            deadline_str = self.df_filings_deadlines.query(
                f'filing_type=="{filing_type[:3]}-{quarter}"'
            )[f"{company_type}"]

            if deadline_str.values.size > 0:
                deadline_str = deadline_str.values[0]
            else:
                print(f"CIK: {self.list_company[0]['cik']}")
                print("Not on time, going into the next quarter")
                return False, None

        except Exception as e:
            print(traceback.format_exc())
            print(f"CIK: {self.list_company[0]['cik']}")
            # If it is not found it means it goes in the next quarter so it is not on time
            return False

        deadline_str = deadline_str.replace("year", str(filing_date_datetime.year))
        deadline_datetime = datetime.strptime(deadline_str, "%Y-%d-%m")
        if filing_date_datetime > deadline_datetime:
            return False, None
        return True, deadline_datetime

    def _get_price_for_filing_date(self, stock_prices_list, filing_date):
        for idx, item in enumerate(stock_prices_list):
            if datetime.fromisoformat(item["timestamp"]) == datetime.fromisoformat(
                filing_date
            ):
                return stock_prices_list[idx], stock_prices_list[idx + 1]
            elif datetime.fromisoformat(item["timestamp"]) > datetime.fromisoformat(
                filing_date
            ):
                return stock_prices_list[idx], stock_prices_list[idx]
        return None, None

    def _get_price_for_filing_deadline_date(self, stock_prices_list, deadline_datetime):
        for idx, item in enumerate(stock_prices_list):
            if datetime.fromisoformat(item["timestamp"]) == deadline_datetime:
                return stock_prices_list[idx], stock_prices_list[idx + 1]
            elif datetime.fromisoformat(item["timestamp"]) > deadline_datetime:
                return stock_prices_list[idx], stock_prices_list[idx]
        return None, None

    def _create_k_fold_config(self, year):
        k_fold_config = {}
        for k in self.k_folds:
            split_type = self.k_fold_rules[year][k]
            k_fold_config[str(k)] = split_type
        return k_fold_config

    def init_prepare_data(self, filing_types_to_process=["10K", "10Q"]):
        imputed_fundamental_data = {}
        for company_year_dict in self.list_company:
            for quarter in company_year_dict["quarters"]:
                for metadata in quarter["metadata"]:
                    if metadata["type"] not in filing_types_to_process:
                        continue

                    curr_input_data = {}

                    filing_on_time, deadline_datetime = self._is_filing_on_time(
                        metadata["type"],
                        quarter["q"],
                        metadata["company_type"],
                        metadata["filing_date"],
                    )

                    if not filing_on_time:
                        # if filing is not on time, we take the price after it is filed
                        t_obj, t_1_obj = self._get_price_for_filing_date(
                            self.list_inflation_prices, metadata["filing_date"]
                        )
                        if not t_obj and not t_1_obj:
                            self.list_of_input_company = []
                            return None
                    else:
                        # if it is on time, we take the price of the deadline
                        t_obj, t_1_obj = self._get_price_for_filing_deadline_date(
                            self.list_inflation_prices, deadline_datetime
                        )
                        if not t_obj and not t_1_obj:
                            self.list_of_input_company = []
                            return None

                    # Fix processing to do only for current period of report
                    fundamental_data_handler = FundamentalDataHandler()
                    fundamental_data_handler.process_company_fundamental_data_for_period(
                        company_year_dict["cik"],
                        self.fundamental_data_dict,
                        t_1_obj["adjusted_close"],
                        metadata["period_of_report"][
                            :10
                        ],  # passing only 2016-12-31 from 2016-12-31T00:00:00
                    )

                    # Save the past available value for all ratios
                    for (
                        ratio_k,
                        value,
                    ) in fundamental_data_handler.company_ratios_period_dict.items():
                        # if a value is available for curr ratio, update
                        if value:
                            imputed_fundamental_data[ratio_k] = value

                    k_fold_config = self._create_k_fold_config(
                        company_year_dict["year"]
                    )

                    curr_input_data["cik"] = company_year_dict["cik"]
                    curr_input_data["year"] = company_year_dict["year"]
                    curr_input_data["type"] = metadata["type"]
                    curr_input_data["q"] = quarter["q"]
                    curr_input_data["mda_section"] = metadata["mda_section"]
                    curr_input_data["risk_section"] = metadata["risk_section"]
                    curr_input_data["company_type"] = metadata["company_type"]
                    curr_input_data["filing_date"] = metadata["filing_date"]
                    curr_input_data["deadline_date"] = deadline_datetime
                    curr_input_data["period_of_report"] = metadata["period_of_report"]
                    curr_input_data["is_filing_on_time"] = filing_on_time
                    curr_input_data["close_price_date"] = t_obj["timestamp"]
                    curr_input_data["close_price"] = t_obj["adjusted_close"]
                    curr_input_data["volume"] = t_obj["volume"]
                    curr_input_data["close_price_next_date"] = t_1_obj["timestamp"]
                    curr_input_data["close_price_next_day"] = t_1_obj["adjusted_close"]
                    curr_input_data["volume_next_day"] = t_1_obj["volume"]
                    curr_input_data["k_fold_config"] = k_fold_config
                    curr_input_data[
                        "fundamental_data"
                    ] = fundamental_data_handler.company_ratios_period_dict
                    curr_input_data[
                        "fundamental_data_imputed"
                    ] = imputed_fundamental_data.copy()

                    self.list_of_input_company.append(curr_input_data)

    def get_percentage_diff(self, first, second):
        diff = second - first
        change = 0
        try:
            if diff > 0:
                change = (diff / first) * 100
            elif diff < 0:
                diff = first - second
                change = -((diff / first) * 100)
        except ZeroDivisionError:
            return float("inf")
        return change

    def create_labels(self, perc_treshold=5):
        for idx, curr_sample_input in enumerate(self.list_of_input_company):
            if idx == len(self.list_of_input_company) - 1:
                curr_sample_input["label"] = None
                curr_sample_input["percentage_change"] = None
                break

            next_sample_input = self.list_of_input_company[idx + 1]

            perc_change = self.get_percentage_diff(
                curr_sample_input["close_price_next_day"],
                next_sample_input["close_price_next_day"],
            )
            if abs(perc_change) < perc_treshold:
                curr_sample_input["label"] = "hold"
            elif perc_change >= perc_treshold:
                curr_sample_input["label"] = "buy"
            else:
                curr_sample_input["label"] = "sell"

            curr_sample_input["percentage_change"] = perc_change

    def separate_paragraphs(self):
        for item in self.list_of_input_company:
            try:
                mda_section_splitted = item["mda_section"].split("\n")
                dict_of_paragraphs_mda = self.reformat_section(mda_section_splitted)
                item["mda_paragraphs"] = dict_of_paragraphs_mda
            except Exception as e:
                print(traceback.format_exc())
                item["mda_paragraphs"] = {}

            try:
                risk_section_splitted = item["risk_section"].split("\n")
                dict_of_paragraphs_risk = self.reformat_section(risk_section_splitted)
                item["risk_paragraphs"] = dict_of_paragraphs_risk

            except Exception as e:
                print(traceback.format_exc())
                item["risk_paragraphs"] = {}

    def reformat_section(self, section_splitted, threshold_for_paragraph=20):
        """
        Things we remove:
        - string ending on ':' (because a table follows),
        - [DATA_TABLE_REMOVED],
        - MDA and QQD section names

        """
        list_of_after_table_numbers = [
            "(1)",
            "(2)",
            "(3)",
            "(4)",
            "(5)",
            "(6)",
            "(7)",
            "(8)",
            "(9)",
        ]
        dict_of_paragraphs = defaultdict(str)
        curr_paragraph_key = None
        paragraph_title = False
        len_section_spitted = len(section_splitted)
        for idx in range(len_section_spitted):
            section_splitted[idx] = section_splitted[idx].strip()
            # print(section_splitted[idx])
            # captures what we want to skip
            if (
                len(section_splitted[idx]) <= 3
                or section_splitted[idx].endswith(":")
                or section_splitted[idx] == "[DATA_TABLE_REMOVED]"
                or "_" in section_splitted[idx]
                or idx == 0
                or idx == len_section_spitted - 1
                or section_splitted[idx].split()[0] in list_of_after_table_numbers
            ):
                continue
            elif len(section_splitted[idx].split()) <= threshold_for_paragraph:
                if paragraph_title:
                    curr_paragraph_key += "|" + section_splitted[idx]
                else:
                    curr_paragraph_key = section_splitted[idx]
                paragraph_title = True
            else:
                dict_of_paragraphs[str(curr_paragraph_key)] += (
                    section_splitted[idx]
                ) + "\n"
                paragraph_title = False

        return dict_of_paragraphs

    def logic(self):
        self.init_prepare_data()
        # if company is not skipped because of lacking stock prices like cik:874499
        if self.list_of_input_company:
            self.create_labels()
            self.separate_paragraphs()
