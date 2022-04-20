from collections import defaultdict


class FundamentalDataHandler:
    def __init__(self) -> None:
        self.list_of_periods_of_reports = None
        self.balance_sheets = None
        self.income_statements = None
        self.cash_flows = None

        self.company_ratios_dict = defaultdict(dict)

    def calculate_average(self, list_of_fundamental_data):
        pass

    def process_company_fundamental_data(
        self, cik, fundamental_data_dict, current_stock_price
    ):
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
                    f"CIK: {cik}, BS: {period_key_bs} | IS: {period_key_is} | CS {period_key_is}"
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
        # ROE
        if (
            self.balance_sheets[period_bs]["totalShareholderEquity"]
            and self.income_statements[period_is]["netIncome"]
        ):
            return (
                self.balance_sheets[period_bs]["totalShareholderEquity"]
                / self.income_statements[period_is]["netIncome"]
            )
        return None

    def _get_return_on_assets(self, period_bs, period_is):
        # ROA
        if (
            self.income_statements[period_is]["netIncome"]
            and self.balance_sheets[period_bs]["totalAssets"]
        ):
            return (
                self.income_statements[period_is]["netIncome"]
                / self.balance_sheets[period_bs]["totalAssets"]
            )
        return None

    def _get_return_on_capital_employed(self, period_bs, period_is):
        # ROCE
        if (
            self.income_statements[period_is]["ebit"]
            and self.balance_sheets[period_bs]["totalAssets"]
            and self.balance_sheets[period_bs]["totalCurrentLiabilities"]
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
            self.income_statements[period]["grossProfit"]
            and self.income_statements[period]["totalRevenue"]
        ):
            return (
                self.income_statements[period]["grossProfit"]
                / self.income_statements[period]["totalRevenue"]
            )

    def _get_operating_profit_margin(self, period):
        # Operating Profit Margin
        if (
            self.income_statements[period]["ebit"]
            and self.income_statements[period]["totalRevenue"]
        ):
            return (
                self.income_statements[period]["ebit"]
                / self.income_statements[period]["totalRevenue"]
            )

    def _get_net_profit_margin(self, period):
        # Net Profit Margin
        if (
            self.income_statements[period]["netIncome"]
            and self.income_statements[period]["totalRevenue"]
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
            self.balance_sheets[period]["totalLiabilities"]
            and self.balance_sheets[period]["totalShareholderEquity"]
        ):
            return (
                self.balance_sheets[period]["totalLiabilities"]
                / self.balance_sheets[period]["totalShareholderEquity"]
            )
        return None

    def _get_equity_ratio(self, period):
        # Equity Ratio
        if (
            self.balance_sheets[period]["totalShareholderEquity"]
            and self.balance_sheets[period]["totalAssets"]
        ):
            return (
                self.balance_sheets[period]["totalShareholderEquity"]
                / self.balance_sheets[period]["totalAssets"]
            )
        return None

    def _get_debt_ratio(self, period):
        # Debt Ratio
        if (
            self.balance_sheets[period]["shortLongTermDebtTotal"]
            and self.balance_sheets[period]["totalAssets"]
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
            self.balance_sheets[period]["totalCurrentAssets"]
            and self.balance_sheets[period]["totalCurrentLiabilities"]
        ):
            return (
                self.balance_sheets[period]["totalCurrentAssets"]
                / self.balance_sheets[period]["totalCurrentLiabilities"]
            )
        return None

    def _get_quick_ratio(self, period):
        # Quick Ratio
        if (
            self.balance_sheets[period]["cashAndShortTermInvestments"]
            and self.balance_sheets[period]["currentNetReceivables"]
            and self.balance_sheets[period]["totalCurrentLiabilities"]
        ):
            return (
                self.balance_sheets[period]["cashAndShortTermInvestments"]
                + self.balance_sheets[period]["currentNetReceivables"]
            ) / self.balance_sheets[period]["totalCurrentLiabilities"]
        return None

    def _get_cash_ratio(self, period):
        # Cash Ratio
        if (
            self.balance_sheets[period]["cashAndCashEquivalentsAtCarryingValue"]
            and self.balance_sheets[period]["totalCurrentLiabilities"]
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
            self.income_statements[period]["ebit"]
            and self.income_statements[period]["interestExpense"]
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
            self.cash_flows[period]["operatingCashflow"]
            and self.cash_flows[period]["capitalExpenditures"]
        ):
            return (
                self.cash_flows[period]["operatingCashflow"]
                / self.cash_flows[period]["capitalExpenditures"]
            )
        return None

    def _get_operating_cash_flow_ratio(self, perios_bs, period_cf):
        # Operating Cash Flow Ratio

        if (
            self.cash_flows[period_cf]["operatingCashflow"]
            and self.balance_sheets[perios_bs]["totalCurrentLiabilities"]
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
            self.income_statements[period_is]["netIncome"]
            and self.cash_flows[period_cf]["dividendPayoutPreferredStock"]
            and self.balance_sheets[perios_bs]["commonStockSharesOutstanding"]
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
            self.income_statements[period_is]["netIncome"]
            and self.balance_sheets[perios_bs]["commonStockSharesOutstanding"]
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
            self.balance_sheets[perios_bs]["commonStockSharesOutstanding"]
            and self.balance_sheets[perios_bs]["cashAndCashEquivalentsAtCarryingValue"]
            and self.balance_sheets[perios_bs]["shortLongTermDebtTotal"]
            and self.income_statements[period_is]["ebitda"]
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
            self.balance_sheets[perios_bs]["commonStockSharesOutstanding"]
            and self.balance_sheets[perios_bs]["cashAndCashEquivalentsAtCarryingValue"]
            and self.balance_sheets[perios_bs]["shortLongTermDebtTotal"]
            and self.income_statements[period_is]["ebit"]
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
            self.balance_sheets[perios_bs]["commonStockSharesOutstanding"]
            and self.balance_sheets[perios_bs]["cashAndCashEquivalentsAtCarryingValue"]
            and self.balance_sheets[perios_bs]["shortLongTermDebtTotal"]
            and self.income_statements[period_is]["totalRevenue"]
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
