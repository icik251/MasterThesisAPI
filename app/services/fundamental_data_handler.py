from collections import defaultdict


class FundamentalDataHandler:
    def __init__(self) -> None:
        self.list_of_periods_of_reports = None
        self.balance_sheets = None
        self.income_statements = None
        self.cash_flows = None

        self.company_ratios_dict = defaultdict(dict)
        self.company_ratios_period_dict = {}

    def process_company_fundamental_data_for_period(
        self, cik, fundamental_data_dict, current_stock_price, period
    ):
        self.balance_sheets = fundamental_data_dict["balance_sheets"]
        self.income_statements = fundamental_data_dict["income_statements"]
        self.cash_flows = fundamental_data_dict["cash_flows"]

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
        # TODO: Fix if equity or income is not a positive number
        # ROE
        if self.balance_sheets.get(period_bs, {}).get(
            "totalShareholderEquity", None
        ) and self.income_statements.get(period_is, {}).get("netIncome", None):
            return (
                self.balance_sheets[period_bs]["totalShareholderEquity"]
                / self.income_statements[period_is]["netIncome"]
            )
        return None

    def _get_return_on_assets(self, period_bs, period_is):
        # ROA
        if (
            self.income_statements.get(period_is, {}).get("netIncome", None)
            and self.balance_sheets.get(period_bs, {}).get("totalAssets", None)
        ):
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
            and self.balance_sheets.get(period_bs, {}).get("totalCurrentLiabilities", None)
        ):
            return self.income_statements[period_is]["ebit"] / (
                self.balance_sheets[period_bs]["totalAssets"]
                - self.balance_sheets[period_bs]["totalCurrentLiabilities"]
            )
        return None

    # Margin Ratios
    def _get_gross_margin_ratio(self, period):
        # Gross Margin Ratio
        if (
            self.income_statements.get(period, {}).get("grossProfit", None)
            and self.income_statements.get(period, {}).get("totalRevenue", None)
        ):
            return (
                self.income_statements[period]["grossProfit"]
                / self.income_statements[period]["totalRevenue"]
            )

    def _get_operating_profit_margin(self, period):
        # Operating Profit Margin
        if (
            self.income_statements.get(period, {}).get("ebit", None)
            and self.income_statements.get(period, {}).get("totalRevenue", None)
        ):
            return (
                self.income_statements[period]["ebit"]
                / self.income_statements[period]["totalRevenue"]
            )

    def _get_net_profit_margin(self, period):
        # Net Profit Margin
        if (
            self.income_statements.get(period, {}).get("netIncome", None)
            and self.income_statements.get(period, {}).get("totalRevenue", None)
        ):
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
        if (
            self.balance_sheets.get(period, {}).get("totalLiabilities", None)
            and self.balance_sheets.get(period, {}).get("totalShareholderEquity", None)
        ):
            return (
                self.balance_sheets[period]["totalLiabilities"]
                / self.balance_sheets[period]["totalShareholderEquity"]
            )
        return None

    def _get_equity_ratio(self, period):
        # Equity Ratio
        if (
            self.balance_sheets.get(period, {}).get("totalShareholderEquity", None)
            and self.balance_sheets.get(period, {}).get("totalAssets", None)
        ):
            return (
                self.balance_sheets[period]["totalShareholderEquity"]
                / self.balance_sheets[period]["totalAssets"]
            )
        return None

    def _get_debt_ratio(self, period):
        # Debt Ratio
        if (
            self.balance_sheets.get(period, {}).get("shortLongTermDebtTotal", None)
            and self.balance_sheets.get(period, {}).get("totalAssets", None)
        ):
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
        if (
            self.balance_sheets.get(period, {}).get("totalCurrentAssets", None)
            and self.balance_sheets.get(period, {}).get("totalCurrentLiabilities", None)
        ):
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
        if (
            self.balance_sheets.get(period, {}).get("cashAndCashEquivalentsAtCarryingValue", None)
            and self.balance_sheets.get(period, {}).get("totalCurrentLiabilities", None)
        ):
            return (
                self.balance_sheets[period]["cashAndCashEquivalentsAtCarryingValue"]
                / self.balance_sheets[period]["totalCurrentLiabilities"]
            )
        return None

    # NOTE: Defensive Interval Ratio skipped

    # Earnings Ratios
    def _get_times_interest_earned_ratio(self, period):
        # Times Interest Earned Ratio

        if (
            self.income_statements.get(period, {}).get("ebit", None)
            and self.income_statements.get(period, {}).get("interestExpense", None)
        ):
            return (
                self.income_statements[period]["ebit"]
                / self.income_statements[period]["interestExpense"]
            )
        return None

    # NOTE: Times Interest Earned (Cash-Basis) Ratio skipped

    # Cash Flow Ratios
    def _get_capex_to_operating_cash_ratio(self, period):
        # CAPEX (Capital Expenditures) to Operating cash Ratio

        if (
            self.cash_flows.get(period, {}).get("operatingCashflow", None)
            and self.cash_flows.get(period, {}).get("capitalExpenditures", None)
        ):
            return (
                self.cash_flows[period]["operatingCashflow"]
                / self.cash_flows[period]["capitalExpenditures"]
            )
        return None

    def _get_operating_cash_flow_ratio(self, perios_bs, period_cf):
        # Operating Cash Flow Ratio

        if (
            self.cash_flows.get(period_cf, {}).get("operatingCashflow", None)
            and self.balance_sheets.get(perios_bs, {}).get("totalCurrentLiabilities", None)
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
            self.income_statements.get(period_is, {}).get("netIncome",None)
            and self.cash_flows.get(period_cf, {}).get("dividendPayoutPreferredStock",None)
            and self.balance_sheets.get(perios_bs, {}).get("commonStockSharesOutstanding",None)
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

        if (
            self.income_statements.get(period_is, {}).get("netIncome", None)
            and self.balance_sheets.get(perios_bs, {}).get("commonStockSharesOutstanding", None)
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
            self.balance_sheets.get(perios_bs, {}).get("commonStockSharesOutstanding", None)
            and self.balance_sheets.get(perios_bs, {}).get("cashAndCashEquivalentsAtCarryingValue", None)
            and self.balance_sheets.get(perios_bs, {}).get("shortLongTermDebtTotal", None)
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
            self.balance_sheets.get(perios_bs, {}).get("commonStockSharesOutstanding", None)
            and self.balance_sheets.get(perios_bs, {}).get("cashAndCashEquivalentsAtCarryingValue", None)
            and self.balance_sheets.get(perios_bs, {}).get("shortLongTermDebtTotal", None)
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
            self.balance_sheets.get(perios_bs, {}).get("commonStockSharesOutstanding", None)
            and self.balance_sheets.get(perios_bs, {}).get("cashAndCashEquivalentsAtCarryingValue", None)
            and self.balance_sheets.get(perios_bs, {}).get("shortLongTermDebtTotal", None)
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
