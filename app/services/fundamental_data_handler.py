from collections import defaultdict

from sklearn.impute import KNNImputer


class FundamentalDataHandler:
    def __init__(self) -> None:
        self.list_of_periods_of_reports = None
        self.balance_sheets = None
        self.income_statements = None
        self.cash_flows = None

        self.company_ratios_dict = defaultdict(dict)
        self.company_ratios_period_dict = {}

        q1 = "12-31"
        q2 = "03-31"
        q3 = "06-30"
        q4 = "09-30"
        self.period_of_reports_mapper = {
            "12-30": q1,
            "12-29": q1,
            "12-26": q1,
            "12-28": q1,
            "03-01": q1,
            "04-01": q2,
            "03-30": q2,
            "03-27": q2,
            "04-03": q2,
            "03-28": q2,
            "04-04": q2,
            "04-27": q2,
            "05-10": q2,
            "07-01": q3,
            "06-29": q3,
            "06-26": q3,
            "07-03": q3,
            "06-27": q3,
            "07-04": q3,
            "10-02": q4,
            "09-25": q4,
            "10-03": q4,
            "09-26": q4,
            "09-28": q4,
            "09-29": q4,
            q1: q1,
            q2: q2,
            q3: q3,
            q4: q4,
        }

    def process_company_fundamental_data_for_period(
        self, cik, fundamental_data_dict, current_stock_price, period
    ):
        self.balance_sheets = fundamental_data_dict["balance_sheets"]
        self.income_statements = fundamental_data_dict["income_statements"]
        self.cash_flows = fundamental_data_dict["cash_flows"]

        # Change period to the according one
        year, month_day = period.split("-", 1)
        month_day_mapped = self.period_of_reports_mapper.get(month_day, None)
        if not month_day_mapped:
            print(f"Error for {cik} for period {period}")
        else:
            period = year + "-" + month_day_mapped

        """
        Profitability Ratios
        """
        # Return Ratios
        self.company_ratios_period_dict["roe"] = self._get_return_on_equity(
            period, period
        )
        self.company_ratios_period_dict["roa"] = self._get_return_on_assets(
            period, period
        )
        self.company_ratios_period_dict["roce"] = self._get_return_on_capital_employed(
            period, period
        )
        # Margin Ratios
        self.company_ratios_period_dict["gross_margin"] = self._get_gross_margin_ratio(
            period
        )
        self.company_ratios_period_dict[
            "operating_profit_margin"
        ] = self._get_operating_profit_margin(period)
        self.company_ratios_period_dict[
            "net_profit_margin"
        ] = self._get_net_profit_margin(period)
        """
            Leverage Ratios
        """
        self.company_ratios_period_dict[
            "debt_to_equity"
        ] = self._get_debt_to_equity_ratio(period)
        self.company_ratios_period_dict["equity"] = self._get_equity_ratio(period)
        self.company_ratios_period_dict["debt"] = self._get_debt_ratio(period)
        """
            Efficiency Ratios
        """
        pass
        """
            Liquidity Ratios
        """
        # Asset Ratios
        self.company_ratios_period_dict["current"] = self._get_current_ratio(period)
        self.company_ratios_period_dict["quick"] = self._get_quick_ratio(period)
        self.company_ratios_period_dict["cash"] = self._get_cash_ratio(period)
        # Earnings Ratios
        self.company_ratios_period_dict[
            "times_interest_earned"
        ] = self._get_times_interest_earned_ratio(period)
        # Cash Flow Ratios
        self.company_ratios_period_dict[
            "capex_to_operating_cash"
        ] = self._get_capex_to_operating_cash_ratio(period)
        self.company_ratios_period_dict[
            "operating_cash_flow"
        ] = self._get_operating_cash_flow_ratio(period, period)
        """
            Multiples Valuation Ratios
        """
        # Price Ratios
        self.company_ratios_period_dict[
            "price_to_earnings"
        ] = self._get_price_to_earnings_ratio_2(period, period, current_stock_price)
        # Enterprise Value Ratios
        self.company_ratios_period_dict["ev_ebitda"] = self._get_ev_ebitda_ratio(
            period, period, current_stock_price
        )
        self.company_ratios_period_dict["ev_ebit"] = self._get_ev_ebit_ratio(
            period, period, current_stock_price
        )
        self.company_ratios_period_dict["ev_revenue"] = self._get_ev_revenue_ratio(
            period, period, current_stock_price
        )

    # REDUNDANT and may contain wrong logic
    def process_company_fundamental_data(
        self, cik, fundamental_data_dict, current_stock_price
    ):
        # Process for all periods
        self.list_of_periods_of_reports_bs = list(
            fundamental_data_dict["balance_sheets"].keys()
        )
        self.list_of_periods_of_reports_is = list(
            fundamental_data_dict["income_statements"].keys()
        )
        self.list_of_periods_of_reports_cf = list(
            fundamental_data_dict["cash_flows"].keys()
        )

        self.balance_sheets = fundamental_data_dict["balance_sheets"]
        self.income_statements = fundamental_data_dict["income_statements"]
        self.cash_flows = fundamental_data_dict["cash_flows"]

        for period_key_bs, period_key_is, period_key_cf in zip(
            self.list_of_periods_of_reports_bs,
            self.list_of_periods_of_reports_is,
            self.list_of_periods_of_reports_cf,
        ):
            if (
                period_key_bs != period_key_is
                or period_key_bs != period_key_is
                or period_key_is != period_key_cf
            ):
                print(
                    f"CIK: {cik}, BS: {period_key_bs} | IS: {period_key_is} | CS {period_key_cf}"
                )
            """
            Profitability Ratios
            """
            # Return Ratios
            self.company_ratios_dict[period_key_bs]["roe"] = self._get_return_on_equity(
                period_key_bs, period_key_is
            )
            self.company_ratios_dict[period_key_bs]["roa"] = self._get_return_on_assets(
                period_key_bs, period_key_is
            )
            self.company_ratios_dict[period_key_bs][
                "roce"
            ] = self._get_return_on_capital_employed(period_key_bs, period_key_is)
            # Margin Ratios
            self.company_ratios_dict[period_key_bs][
                "gross_margin"
            ] = self._get_gross_margin_ratio(period_key_is)
            self.company_ratios_dict[period_key_bs][
                "operating_profit_margin"
            ] = self._get_operating_profit_margin(period_key_is)
            self.company_ratios_dict[period_key_bs][
                "net_profit_margin"
            ] = self._get_net_profit_margin(period_key_is)
            """
                Leverage Ratios
            """
            self.company_ratios_dict[period_key_bs][
                "debt_to_equity"
            ] = self._get_debt_to_equity_ratio(period_key_bs)
            self.company_ratios_dict[period_key_bs]["equity"] = self._get_equity_ratio(
                period_key_bs
            )
            self.company_ratios_dict[period_key_bs]["debt"] = self._get_debt_ratio(
                period_key_bs
            )
            """
                Efficiency Ratios
            """
            pass
            """
                Liquidity Ratios
            """
            # Asset Ratios
            self.company_ratios_dict[period_key_bs][
                "current"
            ] = self._get_current_ratio(period_key_bs)
            self.company_ratios_dict[period_key_bs]["quick"] = self._get_quick_ratio(
                period_key_bs
            )
            self.company_ratios_dict[period_key_bs]["cash"] = self._get_cash_ratio(
                period_key_bs
            )
            # Earnings Ratios
            self.company_ratios_dict[period_key_bs][
                "times_interest_earned"
            ] = self._get_times_interest_earned_ratio(period_key_is)
            # Cash Flow Ratios
            self.company_ratios_dict[period_key_bs][
                "capex_to_operating_cash"
            ] = self._get_capex_to_operating_cash_ratio(period_key_cf)
            self.company_ratios_dict[period_key_bs][
                "operating_cash_flow"
            ] = self._get_operating_cash_flow_ratio(period_key_bs, period_key_cf)
            """
                Multiples Valuation Ratios
            """
            # Price Ratios
            self.company_ratios_dict[period_key_bs][
                "price_to_earnings"
            ] = self._get_price_to_earnings_ratio_2(
                period_key_bs, period_key_is, current_stock_price
            )
            # Enterprise Value Ratios
            self.company_ratios_dict[period_key_bs][
                "ev_ebitda"
            ] = self._get_ev_ebitda_ratio(
                period_key_bs, period_key_is, current_stock_price
            )
            self.company_ratios_dict[period_key_bs][
                "ev_ebit"
            ] = self._get_ev_ebit_ratio(
                period_key_bs, period_key_is, current_stock_price
            )
            self.company_ratios_dict[period_key_bs][
                "ev_revenue"
            ] = self._get_ev_revenue_ratio(
                period_key_bs, period_key_is, current_stock_price
            )

    """
        19 ratios are implemented at the moment.
    """

    """
    Profitability Ratios 
    """
    # Return Ratios
    def _get_return_on_equity(self, period_bs, period_is):
        # Fixed if equity or income is not a positive number
        # ROE
        if self.balance_sheets.get(period_bs, {}).get(
            "totalShareholderEquity", None
        ) and self.income_statements.get(period_is, {}).get("netIncome", None):

            if (
                self.balance_sheets[period_bs]["totalShareholderEquity"] < 0
                and self.income_statements[period_is]["netIncome"] < 0
            ):
                return (
                    -self.balance_sheets[period_bs]["totalShareholderEquity"]
                    / self.income_statements[period_is]["netIncome"]
                )

            return (
                self.balance_sheets[period_bs]["totalShareholderEquity"]
                / self.income_statements[period_is]["netIncome"]
            )
        return None

    def _get_return_on_assets(self, period_bs, period_is):
        # ROA
        if self.income_statements.get(period_is, {}).get(
            "netIncome", None
        ) and self.balance_sheets.get(period_bs, {}).get("totalAssets", None):
            return (
                self.income_statements[period_is]["netIncome"]
                / self.balance_sheets[period_bs]["totalAssets"]
            )
        return None

    def _get_return_on_capital_employed(self, period_bs, period_is):
        # ROCE
        if (
            self.income_statements.get(period_is, {}).get("ebit", None)
            and self.balance_sheets.get(period_bs, {}).get("totalAssets", None)
            and self.balance_sheets.get(period_bs, {}).get(
                "totalCurrentLiabilities", None
            )
        ):
            return self.income_statements[period_is]["ebit"] / (
                self.balance_sheets[period_bs]["totalAssets"]
                - self.balance_sheets[period_bs]["totalCurrentLiabilities"]
            )
        return None

    # Margin Ratios
    def _get_gross_margin_ratio(self, period):
        # Gross Margin Ratio
        if self.income_statements.get(period, {}).get(
            "grossProfit", None
        ) and self.income_statements.get(period, {}).get("totalRevenue", None):
            return (
                self.income_statements[period]["grossProfit"]
                / self.income_statements[period]["totalRevenue"]
            )

    def _get_operating_profit_margin(self, period):
        # Operating Profit Margin
        if self.income_statements.get(period, {}).get(
            "ebit", None
        ) and self.income_statements.get(period, {}).get("totalRevenue", None):
            return (
                self.income_statements[period]["ebit"]
                / self.income_statements[period]["totalRevenue"]
            )

    def _get_net_profit_margin(self, period):
        # Net Profit Margin
        if self.income_statements.get(period, {}).get(
            "netIncome", None
        ) and self.income_statements.get(period, {}).get("totalRevenue", None):
            return (
                self.income_statements[period]["netIncome"]
                / self.income_statements[period]["totalRevenue"]
            )
        return None

    """
    Leverage Ratios
    """

    def _get_debt_to_equity_ratio(self, period):
        # Debt to equity
        # NOTE: Implemented with totalLiabilities (version from financial-ratio cheat sheet)
        if self.balance_sheets.get(period, {}).get(
            "totalLiabilities", None
        ) and self.balance_sheets.get(period, {}).get("totalShareholderEquity", None):
            return (
                self.balance_sheets[period]["totalLiabilities"]
                / self.balance_sheets[period]["totalShareholderEquity"]
            )
        return None

    def _get_equity_ratio(self, period):
        # Equity Ratio
        if self.balance_sheets.get(period, {}).get(
            "totalShareholderEquity", None
        ) and self.balance_sheets.get(period, {}).get("totalAssets", None):
            return (
                self.balance_sheets[period]["totalShareholderEquity"]
                / self.balance_sheets[period]["totalAssets"]
            )
        return None

    def _get_debt_ratio(self, period):
        # Debt Ratio
        if self.balance_sheets.get(period, {}).get(
            "shortLongTermDebtTotal", None
        ) and self.balance_sheets.get(period, {}).get("totalAssets", None):
            return (
                self.balance_sheets[period]["shortLongTermDebtTotal"]
                / self.balance_sheets[period]["totalAssets"]
            )
        return None

    """
    Efficiency Ratios
    """
    # NOTE: Skipping Efficiency ratios for now. They will be here if implemented
    # Accounts Receivable Turnover Ratio
    # Accounts Receivable Days
    # Asset Turnover Ratio
    # Inventory Turnover Ratio
    # Inventory Turnover Days

    """
    Liquidity Ratios
    """
    # Asset Ratios
    def _get_current_ratio(self, period):
        # Current Ratio
        if self.balance_sheets.get(period, {}).get(
            "totalCurrentAssets", None
        ) and self.balance_sheets.get(period, {}).get("totalCurrentLiabilities", None):
            return (
                self.balance_sheets[period]["totalCurrentAssets"]
                / self.balance_sheets[period]["totalCurrentLiabilities"]
            )
        return None

    def _get_quick_ratio(self, period):
        # Quick Ratio
        if (
            self.balance_sheets.get(period, {}).get("cashAndShortTermInvestments", None)
            and self.balance_sheets.get(period, {}).get("currentNetReceivables", None)
            and self.balance_sheets.get(period, {}).get("totalCurrentLiabilities", None)
        ):
            return (
                self.balance_sheets[period]["cashAndShortTermInvestments"]
                + self.balance_sheets[period]["currentNetReceivables"]
            ) / self.balance_sheets[period]["totalCurrentLiabilities"]
        return None

    def _get_cash_ratio(self, period):
        # Cash Ratio
        if self.balance_sheets.get(period, {}).get(
            "cashAndCashEquivalentsAtCarryingValue", None
        ) and self.balance_sheets.get(period, {}).get("totalCurrentLiabilities", None):
            return (
                self.balance_sheets[period]["cashAndCashEquivalentsAtCarryingValue"]
                / self.balance_sheets[period]["totalCurrentLiabilities"]
            )
        return None

    # NOTE: Defensive Interval Ratio skipped

    # Earnings Ratios
    def _get_times_interest_earned_ratio(self, period):
        # Times Interest Earned Ratio

        if self.income_statements.get(period, {}).get(
            "ebit", None
        ) and self.income_statements.get(period, {}).get("interestExpense", None):
            return (
                self.income_statements[period]["ebit"]
                / self.income_statements[period]["interestExpense"]
            )
        return None

    # NOTE: Times Interest Earned (Cash-Basis) Ratio skipped

    # Cash Flow Ratios
    def _get_capex_to_operating_cash_ratio(self, period):
        # CAPEX (Capital Expenditures) to Operating cash Ratio

        if self.cash_flows.get(period, {}).get(
            "operatingCashflow", None
        ) and self.cash_flows.get(period, {}).get("capitalExpenditures", None):
            return (
                self.cash_flows[period]["operatingCashflow"]
                / self.cash_flows[period]["capitalExpenditures"]
            )
        return None

    def _get_operating_cash_flow_ratio(self, perios_bs, period_cf):
        # Operating Cash Flow Ratio

        if self.cash_flows.get(period_cf, {}).get(
            "operatingCashflow", None
        ) and self.balance_sheets.get(perios_bs, {}).get(
            "totalCurrentLiabilities", None
        ):
            return (
                self.cash_flows[period_cf]["operatingCashflow"]
                / self.balance_sheets[perios_bs]["totalCurrentLiabilities"]
            )
        return None

    """
    Multiples Valuation Ratios
    """
    # Price Ratios
    # NOTE: Can also include:
    # 1. Earning Per Share, which is part of P/E
    # 2. Dividend Payout
    # 3. Dividend Yield
    # NOTE: Version from CFI cheat sheet
    def _get_price_to_earnings_ratio_1(
        self, perios_bs, period_is, period_cf, current_stock_price
    ):
        # Price to Earnings Ratio (P/E)

        if (
            self.income_statements.get(period_is, {}).get("netIncome", None)
            and self.cash_flows.get(period_cf, {}).get(
                "dividendPayoutPreferredStock", None
            )
            and self.balance_sheets.get(perios_bs, {}).get(
                "commonStockSharesOutstanding", None
            )
        ):
            return current_stock_price / (
                (
                    self.income_statements[period_is]["netIncome"]
                    - self.cash_flows[period_cf]["dividendPayoutPreferredStock"]
                )
                / self.balance_sheets[perios_bs]["commonStockSharesOutstanding"]
            )
        return None

    # NOTE: Version from https://site.financialmodelingprep.com/developer/docs/formula
    def _get_price_to_earnings_ratio_2(self, perios_bs, period_is, current_stock_price):
        # Price to Earning Ratio (P/E)

        if self.income_statements.get(period_is, {}).get(
            "netIncome", None
        ) and self.balance_sheets.get(perios_bs, {}).get(
            "commonStockSharesOutstanding", None
        ):
            return current_stock_price / (
                self.income_statements[period_is]["netIncome"]
                / self.balance_sheets[perios_bs]["commonStockSharesOutstanding"]
            )
        return None

    # Enterprise Value Ratios
    # NOTE: Check if market cap and net debt are calculated correctly
    def _get_ev_ebitda_ratio(self, perios_bs, period_is, current_stock_price):
        # Enterprise value to EBITDA

        if (
            self.balance_sheets.get(perios_bs, {}).get(
                "commonStockSharesOutstanding", None
            )
            and self.balance_sheets.get(perios_bs, {}).get(
                "cashAndCashEquivalentsAtCarryingValue", None
            )
            and self.balance_sheets.get(perios_bs, {}).get(
                "shortLongTermDebtTotal", None
            )
            and self.income_statements.get(period_is, {}).get("ebitda", None)
        ):
            market_cap = (
                current_stock_price
                * self.balance_sheets[perios_bs]["commonStockSharesOutstanding"]
            )
            net_debt = (
                self.balance_sheets[perios_bs]["shortLongTermDebtTotal"]
                - self.balance_sheets[perios_bs][
                    "cashAndCashEquivalentsAtCarryingValue"
                ]
            )
            enterprise_value = market_cap + net_debt

            return enterprise_value / self.income_statements[period_is]["ebitda"]
        return None

    def _get_ev_ebit_ratio(self, perios_bs, period_is, current_stock_price):
        # Enterprise value to EBIT

        if (
            self.balance_sheets.get(perios_bs, {}).get(
                "commonStockSharesOutstanding", None
            )
            and self.balance_sheets.get(perios_bs, {}).get(
                "cashAndCashEquivalentsAtCarryingValue", None
            )
            and self.balance_sheets.get(perios_bs, {}).get(
                "shortLongTermDebtTotal", None
            )
            and self.income_statements.get(period_is, {}).get("ebit", None)
        ):
            market_cap = (
                current_stock_price
                * self.balance_sheets[perios_bs]["commonStockSharesOutstanding"]
            )
            net_debt = (
                self.balance_sheets[perios_bs]["shortLongTermDebtTotal"]
                - self.balance_sheets[perios_bs][
                    "cashAndCashEquivalentsAtCarryingValue"
                ]
            )
            enterprise_value = market_cap + net_debt

            return enterprise_value / self.income_statements[period_is]["ebit"]
        return None

    def _get_ev_revenue_ratio(self, perios_bs, period_is, current_stock_price):
        # Enterprise value to Revenue

        if (
            self.balance_sheets.get(perios_bs, {}).get(
                "commonStockSharesOutstanding", None
            )
            and self.balance_sheets.get(perios_bs, {}).get(
                "cashAndCashEquivalentsAtCarryingValue", None
            )
            and self.balance_sheets.get(perios_bs, {}).get(
                "shortLongTermDebtTotal", None
            )
            and self.income_statements.get(period_is, {}).get("totalRevenue", None)
        ):
            market_cap = (
                current_stock_price
                * self.balance_sheets[perios_bs]["commonStockSharesOutstanding"]
            )
            net_debt = (
                self.balance_sheets[perios_bs]["shortLongTermDebtTotal"]
                - self.balance_sheets[perios_bs][
                    "cashAndCashEquivalentsAtCarryingValue"
                ]
            )
            enterprise_value = market_cap + net_debt

            return enterprise_value / self.income_statements[period_is]["totalRevenue"]
        return None

    # Methods for using KNN over the fundamental data for filling missing
    def _create_dict_of_industry_id_list_values(self, list_of_input_data):
        dict_of_industry_id_list_values = defaultdict(dict)
        for input_data in list_of_input_data:
            list_of_current_values_to_add = []
            for kpi in input_data["fundamental_data"]:
                list_of_current_values_to_add.append(
                    (kpi, input_data["fundamental_data_imputed_past"].get(kpi, None))
                )
            dict_of_industry_id_list_values[input_data["industry"]][
                input_data["_id"]
            ] = (input_data["is_filing_on_time"], list_of_current_values_to_add)
        return dict_of_industry_id_list_values

    def knn_imputer_logic(self, list_of_input_data, n_neighbours):
        dict_of_industry_id_list_values = self._create_dict_of_industry_id_list_values(
            list_of_input_data
        )

        for (
            industry_key,
            id_dict_list_values,
        ) in dict_of_industry_id_list_values.items():
            list_for_industry_imputer = []
            list_of_all_for_industry = []
            initial_kpi_idx_mappper = {}
            create_imputer_for_industry = False
            for id_k, (on_time, tuple_kpi_value) in id_dict_list_values.items():
                curr_id_list = [None] * len(tuple_kpi_value)
                # Fill initial kpi idx mapper on first possible data
                if on_time and not initial_kpi_idx_mappper:
                    for idx, (kpi, value) in enumerate(tuple_kpi_value):
                        initial_kpi_idx_mappper[kpi] = idx
                        curr_id_list[idx] = value
                        if not value:
                            create_imputer_for_industry = True

                    list_for_industry_imputer.append((id_k, curr_id_list))
                    list_of_all_for_industry.append((id_k, curr_id_list))

                elif on_time and initial_kpi_idx_mappper:
                    for idx, (kpi, value) in enumerate(tuple_kpi_value):
                        curr_id_list[idx] = value
                        if not value:
                            create_imputer_for_industry = True

                    list_for_industry_imputer.append((id_k, curr_id_list))
                    list_of_all_for_industry.append((id_k, curr_id_list))

                elif not on_time:
                    for idx, (kpi, value) in enumerate(tuple_kpi_value):
                        curr_id_list[idx] = value
                        if not value:
                            create_imputer_for_industry = True
                    list_of_all_for_industry.append((id_k, curr_id_list))

            # If there is None, create KNNImputer with the following list
            if create_imputer_for_industry:
                curr_imputer = KNNImputer(n_neighbors=n_neighbours)
                list_for_imputation = [i[1] for i in list_for_industry_imputer]
                if not list_for_imputation:
                    # If Imputer can't be created
                    yield industry_key, {}
                    break

                curr_imputer.fit(list_for_imputation)

                for id, list_of_values_for_id in list_of_all_for_industry:
                    dict_of_curr_imputed_full = {}
                    if None in list_of_values_for_id:
                        imputed_list_of_values_for_id = curr_imputer.transform(
                            [list_of_values_for_id]
                        ).tolist()[0]
                    else:
                        imputed_list_of_values_for_id = list_of_values_for_id

                    for kpi, idx in initial_kpi_idx_mappper.items():
                        dict_of_curr_imputed_full[kpi] = imputed_list_of_values_for_id[
                            initial_kpi_idx_mappper[kpi]
                        ]

                    yield id, dict_of_curr_imputed_full
            # Else return them one by one
            else:
                for id, list_of_values_for_id in list_of_all_for_industry:
                    dict_of_curr_imputed_full = {}

                    for kpi, idx in initial_kpi_idx_mappper.items():
                        dict_of_curr_imputed_full[kpi] = list_of_values_for_id[
                            initial_kpi_idx_mappper[kpi]
                        ]
                    yield id, dict_of_curr_imputed_full
    