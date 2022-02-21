import os
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from bs4 import BeautifulSoup


class SECScraper:
    def __init__(self, company_dict: dict, geckodriver_path: str) -> None:
        self.cik = company_dict["cik"]
        self.name = company_dict["name"]
        self.year = company_dict["year"]
        self.quarter = company_dict["quarter"]
        self.type = company_dict["type"]
        self.filing_date = company_dict["filing_date"]
        self.html_path = company_dict["html_path"]
        self.geckodriver_path = geckodriver_path

        self.base_url = "https://www.sec.gov/Archives/"
        self.soup = None
        self.htm_url = None
        self.dict_date_info = dict()

    def create_soup(self) -> None:
        opts = Options()
        opts.headless = True
        ser = Service(self.geckodriver_path)
        browser = Firefox(options=opts, service=ser)

        # find another way to detect error code
        if "errorPageContainer" in [
            elem.get_attribute("id")
            for elem in browser.find_elements_by_css_selector("body > div")
        ]:
            browser.quit()
            raise Exception
        else:
            browser.get(os.path.join(self.base_url, self.html_path))

        self.soup = BeautifulSoup(browser.page_source, "html.parser")
        browser.quit()

    def extract_htm_url(self) -> None:
        filing_url = self._extract_filing_url()

        if not filing_url:
            return

        self.htm_url = os.path.join(
            self.base_url,
            self.html_path.replace("index.html", "").replace("-", "")
            + "/"
            + filing_url,
        )

    def extract_date_info(self) -> None:
        list_of_forms = self.soup.find_all("div", class_="formGrouping")

        for form in list_of_forms:
            curr_key = None
            curr_value = None
            for possible_div in form.contents:
                if possible_div == "\n":
                    continue

                text_of_div = possible_div.text
                if not self._is_num_in_string(text_of_div):
                    curr_key = text_of_div
                else:
                    curr_value = text_of_div

                if curr_key and curr_value:
                    self.dict_date_info[curr_key] = curr_value
                    curr_key = None
                    curr_value = None

    def _is_num_in_string(self, s):
        return any(i.isdigit() for i in s)

    def _extract_filing_url(self) -> str:
        table = (
            self.soup.find("table", {"class": "tableFile"}).find("tbody").find_all("tr")
        )
        for row in table:
            cells = row.find_all("td")
            if cells:
                curr_type = cells[3]
                curr_doc = cells[2]
                if self.type in curr_type and curr_doc.get_text():
                    return curr_doc.get_text().split()[0]
                if curr_doc.get_text().split()[0].endswith(".txt"):
                    return curr_doc.get_text().split()[0]

        return None

    def get_htm_url(self):
        return self.htm_url

    def get_date_info(self):
        return self.dict_date_info

    def logic(self):
        self.create_soup()
        self.extract_htm_url()
        self.extract_date_info()


# edgar/data/1064728/0001064728-21-000008-index.html
sec_scraper = SECScraper(
    {
        "cik": 123,
        "name": "ASD",
        "year": 2000,
        "quarter": 1,
        "type": "10-K",
        "filing_date": None,
        "html_path": "edgar/data/1064728/0001064728-99-000003-index.html",
    },
    "D:/PythonProjects/MasterThesisAPI/geckodriver.exe",
)

sec_scraper.logic()
