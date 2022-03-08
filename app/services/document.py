"""
    secedgartext: extract text from SEC corporate filings
    Copyright (C) 2017  Alexander Ions

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import time
from datetime import datetime
import copy
import os
from abc import ABCMeta


class Document(object):
    __metaclass__ = ABCMeta

    def __init__(self, file_path, doc_text, extraction_method):
        self._file_path = file_path
        self.doc_text = doc_text
        self.extraction_method = extraction_method
        self.log_cache = []

    def get_excerpt(
        self,
        input_text,
        form_type,
        metadata_master,
        master_search_terms,
        skip_existing_excerpts,
    ):
        """

        :param input_text:
        :param form_type:
        :param metadata_master:
        :param skip_existing_excerpts:
        :return:
        """
        start_time = time.process_time()
        self.prepare_text()
        prep_time = time.process_time() - start_time

        dict_result = {}
        for section_search_terms in master_search_terms[form_type]:
            start_time = time.process_time()
            metadata = copy.copy(metadata_master)
            warnings = []
            section_name = section_search_terms["itemname"]
            section_name_actual = section_search_terms["sectionname"]

            # print("document, 52")
            # print(section_search_terms)
            search_pairs = section_search_terms[self.search_terms_type()]
            (
                text_extract,
                extraction_summary,
                start_text,
                end_text,
                warnings,
            ) = self.extract_section(search_pairs)

            time_elapsed = time.process_time() - start_time
            # metadata.extraction_method = self.extraction_method
            metadata.section_name = section_name
            if start_text:
                start_text = start_text.replace('"', "'")
            if end_text:
                end_text = end_text.replace('"', "'")
            metadata.endpoints = [start_text, end_text]
            metadata.warnings = warnings
            metadata.time_elapsed = round(prep_time + time_elapsed, 1)
            metadata.section_end_time = str(datetime.utcnow())
            if text_extract:
                dict_result[section_name_actual] = text_extract

            else:
                print(f"No data for {section_name_actual}")

        return dict_result, metadata

    def prepare_text(self):
        # handled in child classes
        pass
