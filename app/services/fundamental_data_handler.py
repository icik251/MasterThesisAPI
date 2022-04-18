class FundamentalDataHandler:
    def __init__(self) -> None:
        self.list_of_periods_of_reports = None
        self.balance_sheets = None
        self.income_statements = None
        self.cash_flows = None

    def calculate_average(self, list_of_fundamental_data):
        pass

    def process_company_fundamental_data(self, fundamental_data_dict):
        self.list_of_periods_of_reports = list(
            fundamental_data_dict["balance_sheets"].keys()
        )

        self.balance_sheets = fundamental_data_dict["balance_sheets"]
        self.income_statements = fundamental_data_dict["income_statements"]
        self.cash_flows = fundamental_data_dict["cash_flows"]

    # Ratios
    def _get_return_on_equity(self):
        # ROE
        if (
            self.balance_sheets["totalShareholderEquity"]
            and self.income_statements["netIncome"]
        ):
            return (
                self.balance_sheets["totalShareholderEquity"]
                / self.income_statements["netIncome"]
            )
        return None

    def _get_return_on_assets(self):
        # ROA
        if self.income_statements["netIncome"] and self.balance_sheets["totalAssets"]:
            return (
                self.income_statements["netIncome"] / self.balance_sheets["totalAssets"]
            )
        return None

    def _get_return_on_capital_employed(self):
        # ROCE
        if (
            self.income_statements["ebit"]
            and self.balance_sheets["totalAssets"]
            and self.balance_sheets["totalCurrentLiabilities"]
        ):
            return self.balance_sheets["ebit"] / (
                self.balance_sheets["totalAssets"]
                - self.balance_sheets["totalCurrentLiabilities"]
            )
        return None

    def _get_gross_margin_ratio(self):
        # Gross Margin Ratio
        if (
            self.income_statements["grossProfit"]
            and self.income_statements["totalRevenue"]
        ):
            return (
                self.income_statements["grossProfit"]
                / self.income_statements["totalRevenue"]
            )

    def _get_operating_profit_margin(self):
        # Operating Profit Margin
        if self.income_statements["ebit"] and self.income_statements["totalRevenue"]:
            return (
                self.income_statements["ebit"] / self.income_statements["totalRevenue"]
            )

    def _get_net_profit_margin(self):
        # Net Profit Margin
        if (
            self.income_statements["netIncome"]
            and self.income_statements["totalRevenue"]
        ):
            return (
                self.income_statements["netIncome"]
                / self.income_statements["totalRevenue"]
            )
        return None

    def _get_debt_to_equity_ratio(self):
        # Debt to equity
        # NOTE: Implemented with totalLiabilities (one cheat sheet shows it like that)
        if (
            self.balance_sheets["totalLiabilities"]
            and self.balance_sheets["totalShareholderEquity"]
        ):
            return (
                self.balance_sheets["totalLiabilities"]
                / self.balance_sheets["totalShareholderEquity"]
            )
        return None

    def _get_equity_ratio(self):
        # Equity Ratio
        if (
            self.balance_sheets["totalShareholderEquity"]
            and self.balance_sheets["totalAssets"]
        ):
            return (
                self.balance_sheets["totalShareholderEquity"]
                / self.balance_sheets["totalAssets"]
            )
        return None

    def _get_debt_ratio(self):
        # Debt Ratio
        if (
            self.balance_sheets["shortLongTermDebtTotal"]
            and self.balance_sheets["totalAssets"]
        ):
            return (
                self.balance_sheets["shortLongTermDebtTotal"]
                / self.balance_sheets["totalAssets"]
            )
        return None

    # NOTE: Skipping Efficiency ratios for now. They will be here if implemented

    def _get_current_assets(self):
        # Current Ratio
        if (
            self.balance_sheets["totalCurrentAssets"]
            and self.balance_sheets["totalCurrentLiabilities"]
        ):
            return (
                self.balance_sheets["totalCurrentAssets"]
                / self.balance_sheets["totalCurrentLiabilities"]
            )
        return None

    def _get_quick_ratio(self):
        # Quick Ratio
        if (
            self.balance_sheets["cashAndShortTermInvestments"]
            and self.balance_sheets["currentNetReceivables"]
            and self.balance_sheets["totalCurrentLiabilities"]
        ):
            return (
                self.balance_sheets["cashAndShortTermInvestments"]
                + self.balance_sheets["currentNetReceivables"]
            ) / self.balance_sheets["totalCurrentLiabilities"]
        return None
    
    def _get_cash_ratio(self):
        # Cash Ratio
        if self.balance_sheets["cashAndCashEquivalentsAtCarryingValue"] and self.balance_sheets["totalCurrentLiabilities"]:
            return self.balance_sheets["cashAndCashEquivalentsAtCarryingValue"] / self.balance_sheets["totalCurrentLiabilities"]
        return None
    
    
