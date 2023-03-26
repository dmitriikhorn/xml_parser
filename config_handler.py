import copy
from pathlib import Path
import lxml.etree as ET
from lxml.etree import _Element, XMLSyntaxError, _ElementTree
from xml_parser_helpers import xml_audit_logger
import xml_parser_dc as dc
import yaml


class XMLRoot:

    def __init__(self, config_file: Path):
        self.config_file: Path = config_file
        self.config_file_name = config_file.__str__()
        self.xml_root: _ElementTree = self.parse_configuration()

    def parse_configuration(self) -> _ElementTree | None:
        """
        Open and parse XML document representing configuration
        :return: Parsed configuration as ElementTree object
        """
        if not self.config_file.is_file():
            xml_audit_logger.error(f'File "{self.config_file_name}" does not exists')
            return
        try:
            return ET.parse(self.config_file_name)
        except OSError:
            xml_audit_logger.error(f'Can not open the file "{self.config_file_name}"')
        except XMLSyntaxError as err_code:
            xml_audit_logger.error(f'Error parsing XML-document "{self.config_file_name}": {err_code}')


class XpathConstructor:
    # TODO: Refactor to get data from DB(?)/API(?)

    def __init__(self, input_path: list):
        self.parsed_elements: list = self.convert_xpath_to_dataclass(input_path)

    @staticmethod
    def parse_filters(raw_filter_list: list | None) -> list[dc.FilterElement]:
        """
        Parse list of filtered parameters into list of custom dataclasses FilterElement
        :param raw_filter_list:
        :return: List of FilterElement objects
        """
        parsed_filters: list = []
        if not raw_filter_list:
            return parsed_filters
        for raw_filter in raw_filter_list:
            raw_filter: dict
            filter_elem = dc.FilterElement()
            filter_elem.filter_path = raw_filter.get("filter_path")
            filter_elem.regexp = raw_filter.get("regexp")
            parsed_filters.append(filter_elem)
        return parsed_filters

    def convert_xpath_to_dataclass(self, raw_list_of_elem: list) -> list[dc.PathElement]:
        """
        Convert xpath-request coming from YANG model (DB?)-format to custom dataclass
        :param raw_list_of_elem: List of elements in the xpath
        :return: List of custom dataclass objects PathElement (representing xpath-request)
        """
        parsed_elements: list = []
        for elem in raw_list_of_elem:
            elem: dict
            path_elem = dc.PathElement()
            path_elem.name = elem.get("name")
            path_elem.filters = self.parse_filters(elem.get("filters"))
            parsed_elements.append(path_elem)
        return parsed_elements


class ConfigHandler:

    def __init__(self, xml_root: _ElementTree):
        self.xml_root: _ElementTree = xml_root
        self.namespace_map: dict = self.get_namespace_mapping()
        self.inverse_namespace_map = {f"{{{v}}}": k for k, v in self.namespace_map.items()}
        self.namespace_prefix: str = "ns:" if "ns" in self.namespace_map else ""

    def get_namespace_mapping(self) -> dict:
        """
        Get namespaces from XML header
        Add REGEX to the NS
        :return: Namespace mapping as dictionary
        """
        ns_map: dict = self.xml_root.getroot().nsmap
        ns_map["re"] = "http://exslt.org/regular-expressions"
        if None in ns_map:
            ns_map["ns"] = ns_map.pop(None)
        return ns_map

    def prepend_namespace(self, x_path: str) -> str:
        """
        Prepend namespace to the path
        :param x_path: XPATH string representation
        :return: Updated XPATH
        """
        splitted_path: list = [self.namespace_prefix + path for path in x_path.split("/")]
        return "/".join(splitted_path)

    def convert_xpath_to_string(self, parsed_xpath: list[dc.PathElement]) -> str:
        """
        Convert parsed XPATH to string representation with prepended namespaces, filters or indexes
        :param parsed_xpath: Parsed representation of XPATH
        :return: String representation XPATH query
        """
        xpath: str = ""
        last_item_id: int = len(parsed_xpath) - 1
        for idx, elem in enumerate(parsed_xpath):
            xpath += self.namespace_prefix
            xpath += elem.name
            if elem.sibling_id:
                xpath += f'[{elem.sibling_id}]'
            else:
                for filter_id in elem.filters:
                    xpath += f'[re:match({self.prepend_namespace(filter_id.filter_path)}, "{filter_id.regexp}")]'
            xpath += "/" if idx != last_item_id else ""
        return xpath

    def get_position_index(self, node: _Element, element_tag: str) -> int:
        """
        Run preceding-sibling query to get index among siblings
        :param node: XML node element
        :param element_tag: Tag of an element with prepended NS
        :return: Index number as integer
        """
        siblings: list = node.xpath(f"./preceding-sibling::{self.namespace_prefix}{element_tag}",
                                    namespaces=self.namespace_map)
        return len(siblings) + 1

    def get_indexed_path(self, parsed_xpath: list[dc.PathElement], node: _Element) -> list[dc.PathElement]:
        """
        Parsing ancestors(except node 'configure') and getting indexes of the Elements in the path
        :param parsed_xpath: Parsed representation of XPATH
        :param node: XML node element
        :return: Updated list of responses to XPATH query
        """
        updated_xpath: list[dc.PathElement] = copy.deepcopy(parsed_xpath)
        node_ancestors: list[_Element] = node.xpath('./ancestor-or-self::*')
        for id in range(1, len(node_ancestors)):
            updated_xpath[id - 1].sibling_id = self.get_position_index(node_ancestors[id], updated_xpath[id - 1].name)
        return updated_xpath

    @staticmethod
    def build_indexed_query(response: list[dc.PathElement]) -> list[dc.FilterElement]:
        """
        Build explicit indexed path to get a data from XML
        :param response: Parsed response from to the XPATH query
        :return: List of elements where filter is applied
        """
        root_path: str = ""
        elements_with_data: list = list()
        for path_element in response:
            root_path += f"{path_element.name}[{path_element.sibling_id}]/"
            if path_element.filters:
                for fltr in path_element.filters:
                    fltr.indexed_query = root_path + fltr.filter_path
                    elements_with_data.append(fltr)
        return elements_with_data

    def run_indexed_query(self, indexed_queries: list[dc.FilterElement]) -> list[dc.FilterElement]:
        """
        Run explicit indexed path XPATH queries and record the results to value attribute
        Response to the query is always unique, i.e. response list's length == 1
        :param indexed_queries: List of elements where filter is applied
        :return: List of elements where filter is applied with updated results
        """
        updated_indexed_queries: list[dc.FilterElement] = copy.deepcopy(indexed_queries)
        for query in updated_indexed_queries:
            xpath: str = self.prepend_namespace(query.indexed_query)
            results: list[_Element] = self.run_xpath_query(xpath)
            if len(results) == 1:
                query.value = results[0].text
            else:
                xml_audit_logger.error(f'Response to the explicit query is more than one: "{query.indexed_query}"')
        return updated_indexed_queries

    def process_query_pipeline(self, parsed_xpath: list[dc.PathElement]) -> list[list[dc.FilterElement]]:
        """
        Process Query: convert XPATH to string => run query => process reply
        :param parsed_xpath: Parsed representation of XPATH
        :return: List of elements with activated filter and values
        """
        string_xpath: str = self.convert_xpath_to_string(parsed_xpath)
        query_response: list[_Element] = self.run_xpath_query(string_xpath)
        indexed_paths_responses = [self.get_indexed_path(parsed_xpath, result_node) for result_node in query_response]
        indexed_queries = [self.build_indexed_query(response) for response in indexed_paths_responses]
        result_list = [self.run_indexed_query(query) for query in indexed_queries]
        return result_list

    def run_xpath_query(self, x_path: str) -> list[_Element]:
        """
        Run absolute XPATH query
        :param x_path: String representation of XPATH
        :return: List of XPATH Elements
        """
        return self.xml_root.xpath(x_path, namespaces=self.namespace_map)


if __name__ == "__main__":

    with open("request_input.yml", "r") as f:
        request_input = yaml.safe_load(f)

    converted_path = XpathConstructor(request_input)
    r2_cfg: Path = Path("configurations/r2.xml")
    if test_xml_root := XMLRoot(r2_cfg).xml_root:
        test_cfg = ConfigHandler(test_xml_root)
        resp = test_cfg.process_query_pipeline(converted_path.parsed_elements)
        # A class for IN/OUT API
        print("debug")
