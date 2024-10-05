import pytest
from xml_parser_dc import FilterElement, PathElement
import yaml
from config_handler import XpathConstructor
from xml_parser_exceptions import IncorrectXmlParserApiRequest
from pydantic.error_wrappers import ValidationError

test_filter_1: list = [{'filter_path': 'user-profile-parent/user-profile-child', 'regexp': 'target'},
                       {'filter_path': 'default-action', 'regexp': '.*'}]
filter_1_out: list = [FilterElement(filter_path='user-profile-parent/user-profile-child', regexp='target', indexed_query=None, unindexed_path=None, is_a_path=True),
                           FilterElement(filter_path='default-action', regexp='.*', indexed_query=None, unindexed_path=None, is_a_path=True)]

test_filter_2: list = [{'filter_path': 'default-action', 'regexp': ''}]
filter_2_out: list = [FilterElement(filter_path='default-action', regexp='.*', indexed_query=None, unindexed_path=None, is_a_path=True)]


test_filter_3: list = [{'filter_path': '', 'regexp': '.*'}]
filter_3_out: list = [FilterElement(filter_path='text()', regexp='.*', indexed_query=None, unindexed_path=None, is_a_path=False)]

test_filter_4: list = []
filter_4_out: list = []

test_filter_5: list = [{'filter_path_fail': 'wrong_path'}]


@pytest.mark.parametrize("input_filter, expected_result", [
    (test_filter_1, filter_1_out),
    (test_filter_2, filter_2_out),
    (test_filter_3, filter_3_out),
    (test_filter_4, filter_4_out),
])
def test_parse_filters(input_filter, expected_result):
    result = XpathConstructor.parse_filters(input_filter)
    assert result == expected_result


@pytest.mark.parametrize("input_filter", [test_filter_5])
def test_parse_filters_exceptions(input_filter):
    with pytest.raises((TypeError, ValueError)) as e_info:
        XpathConstructor.parse_filters(input_filter)


test_xpath_1: list = [{'name': 'system'}, {'name': 'security', 'filters': test_filter_2}]
xpath_1_out: list = [PathElement(name='system', sibling_id=None, filters=[], indexed_path=None),  PathElement(name='security', sibling_id=None, filters=filter_2_out, indexed_path=None)]

test_xpath_2: list = [{'filters': []}, {'name': 'security', 'filters': test_filter_2}]
test_xpath_3: list = [{'name': ''}, {'name': 'security', 'filters': test_filter_2}]


@pytest.mark.parametrize("input_xpath, expected_result", [
    (test_xpath_1, xpath_1_out),
])
def test_convert_xpath_to_dataclass(input_xpath, expected_result):
    result = XpathConstructor(input_xpath).convert_xpath_to_dataclass()
    assert result == expected_result


@pytest.mark.parametrize("input_xpath", [test_xpath_2, test_xpath_3])
def test_convert_xpath_to_dataclass_exceptions(input_xpath):
    with pytest.raises((IncorrectXmlParserApiRequest, ValidationError)) as e_info:
        XpathConstructor(input_xpath).convert_xpath_to_dataclass()
