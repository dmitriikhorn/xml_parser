import copy
from pathlib import Path
import lxml.etree as ET
from lxml.etree import _Element, XMLSyntaxError, _ElementTree
from xml_parser_helpers import xml_audit_logger
import xml_parser_dc as dc
import yaml
from xml_parser_exceptions import XmlConfigurationLoadError


class XMLRoot:

    def __init__(self, config_file: Path):
        self.config_file: Path = config_file
        self.config_file_name = config_file.__str__()
        self.xml_root: _ElementTree = self.get_xml_root()

    def get_xml_root(self) -> _ElementTree | None:
        """
        Open and parse XML document representing device configuration
        :return: XML_Root object, i.e. parsed configuration
        """
        if not self.config_file.is_file():
            xml_audit_logger.error(f'File "{self.config_file_name}" does not exists')
            raise XmlConfigurationLoadError(f'Configuration file "{self.config_file_name}" could not be found')
        try:
            return ET.parse(self.config_file_name)
        except OSError:
            xml_audit_logger.error(f'Can not open the file "{self.config_file_name}"')
            raise XmlConfigurationLoadError(f'Configuration file "{self.config_file_name}" could not be loaded')
        except XMLSyntaxError as err_code:
            xml_audit_logger.error(f'Error parsing XML-document "{self.config_file_name}": {err_code}')
            raise XmlConfigurationLoadError(f'Configuration file "{self.config_file_name}" has not correct XML format')


class XpathConstructor:

    def __init__(self, input_path: list):
        self.input_path: list[dict] = input_path

    @staticmethod
    def parse_filters(raw_filter_list: list | None) -> list[dc.FilterElement]:
        """
        Parse list of filtered parameters into list of custom dataclasses FilterElement
        :param raw_filter_list:
        :return: List of FilterElement objects
        """
        if not raw_filter_list:
            return list()
        parsed_filters: list[dc.FilterElement] = [dc.FilterElement(**raw_filter) for raw_filter in raw_filter_list]
        return parsed_filters

    def convert_xpath_to_dataclass(self) -> list[dc.PathElement]:
        """
        Convert xpath-request coming from YANG model (DB?)-format to custom dataclass
        :return: List of custom dataclass objects PathElement (representing xpath-request)
        """
        parsed_elements: list = []
        for elem in self.input_path:
            path_elem = dc.PathElement(
                name=elem.get("name"),
                filters=self.parse_filters(elem.get("filters"))
            )
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
        splitted_path: list = [self.namespace_prefix + path for path in x_path.strip("/").split("/")]
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
                    filter_path: str = self.prepend_namespace(filter_id.filter_path) if filter_id.is_a_path \
                        else filter_id.filter_path
                    xpath += f'[re:match({filter_path}, "{filter_id.regexp}")]'
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
        for node_id in range(1, len(node_ancestors)):
            updated_xpath[node_id - 1].sibling_id = \
                self.get_position_index(node_ancestors[node_id], updated_xpath[node_id - 1].name)
        return updated_xpath

    @staticmethod
    def prepare_queries(response: list[dc.PathElement]) -> list[dc.FilterElement]:
        """
        Build explicit indexed path to get a data from XML (alongside with unindexed path, to use in an API)
        :param response: Parsed response from to the XPATH query
        :return: List of elements where filter is applied
        """
        elements_with_filters: list = list()
        root_path: str = ""
        idx_root_path: str = ""
        for path_element in response:
            root_path += f"{path_element.name}/"
            idx_root_path += f"{path_element.name}[{path_element.sibling_id}]/"
            if path_element.filters:
                for fltr in path_element.filters:
                    fltr.indexed_query = idx_root_path + fltr.filter_path if fltr.is_a_path else idx_root_path
                    fltr.unindexed_path = root_path + fltr.filter_path if fltr.is_a_path else root_path
                    elements_with_filters.append(fltr)
        return elements_with_filters

    def run_indexed_query(self, indexed_queries: list[dc.FilterElement]) -> list[dc.ResultItem]:
        """
        Run explicit indexed XPATH queries and record the results to the 'value' attribute
        Response to the query is always unique, i.e. response list's length == 1
        :param indexed_queries: List of elements where filter is applied
        :return: List of elements where filter is applied with updated values
        """
        explicit_queries_results = list()
        for query in indexed_queries:
            query_result = dc.ResultItem()
            xpath: str = self.prepend_namespace(query.indexed_query)
            results: list[_Element] = self.run_xpath_query(xpath)
            if len(results) == 1:
                query_result.path_attribute = query.unindexed_path
                query_result.value = results[0].text
                explicit_queries_results.append(query_result)
            else:
                xml_audit_logger.error(f'Response to the explicit query is more than one: "{query.indexed_query}"')
        return explicit_queries_results

    def process_query_pipeline(self, parsed_xpath: list[dc.PathElement]) -> list[list[dc.ResultItem]]:
        """
        Process Query: convert XPATH to string => run query => process reply
        :param parsed_xpath: Parsed representation of XPATH
        :return: List of elements with activated filter and values
        """
        string_xpath: str = self.convert_xpath_to_string(parsed_xpath)
        query_response: list[_Element] = self.run_xpath_query(string_xpath)
        indexed_paths_responses = [self.get_indexed_path(parsed_xpath, result_node) for result_node in query_response]
        indexed_queries = [self.prepare_queries(response) for response in indexed_paths_responses]
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

    converted_path = XpathConstructor(request_input).convert_xpath_to_dataclass()
    r2_cfg: Path = Path("configurations/r2.xml")
    if test_xml_root := XMLRoot(r2_cfg).get_xml_root():
        test_cfg = ConfigHandler(test_xml_root)
        resp = test_cfg.process_query_pipeline(converted_path)
        print("debug")
