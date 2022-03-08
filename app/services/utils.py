import sys
import time
import json
from core import settings
from copy import copy

"""Create search_terms_regex, which stores the patterns that we
use for identifying sections in each of EDGAR documents types
"""


def load_search_terms(path_to_search_terms=settings.PATH_TO_SEARCH_TERMS):
    with open(path_to_search_terms, "r") as f:
        json_text = f.read()
        search_terms = json.loads(json_text)
        if not search_terms:
            pass
            # logger.error('Search terms file is missing or corrupted: ' +
            #       f.name)

        search_terms_regex = copy(search_terms)
        for filing in search_terms:
            for idx, section in enumerate(search_terms[filing]):
                for format in ["txt", "html"]:
                    for idx2, pattern in enumerate(search_terms[filing][idx][format]):
                        for startend in ["start", "end"]:
                            regex_string = search_terms[filing][idx][format][idx2][
                                startend
                            ]
                            regex_string = regex_string.replace("_", "\\s{,5}")
                            regex_string = regex_string.replace("\n", "\\n")
                            search_terms_regex[filing][idx][format][idx2][
                                startend
                            ] = regex_string

    return search_terms


def requests_get(url, params=None):
    """retrieve text via url, fatal error if no internet connection available
    :param url: source url
    :return: text retriieved
    """
    import requests, random

    retries = 0
    success = False
    hdr = {
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Mobile Safari/537.36"
    }
    while (not success) and (retries <= 20):
        # wait for an increasingly long time (up to a day) in case internet
        # connection is broken. Gives enough time to fix connection or SEC site
        try:
            # to test the timeout functionality, try loading this page:
            # http://httpstat.us/200?sleep=20000  (20 seconds delay before page loads)
            r = requests.get(url, headers=hdr, params=params, timeout=10)
            success = True
            # facility to add a pause to respect SEC EDGAR traffic limit
            # https://www.sec.gov/privacy.htm#security
            time.sleep(5)
        except requests.exceptions.RequestException as e:
            wait = (retries ^ 3) * 20 + random.randint(1, 5)
            # logger.warning(e)
            # logger.info('URL: %s' % url)
            # logger.info(
            #     'Waiting %s secs and re-trying...' % wait)
            time.sleep(wait)
            retries += 1
    if retries > 10:
        # logger.error('Download repeatedly failed: %s',
        #              url)
        sys.exit("Download repeatedly failed: %s" % url)
    return r
