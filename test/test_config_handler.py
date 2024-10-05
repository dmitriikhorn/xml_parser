import pytest
from xml_parser_exceptions import XmlConfigurationLoadError
from config_handler import XMLRoot
from pathlib import Path
from lxml.etree import _ElementTree
from config_handler import ConfigHandler


current_dir: Path = Path(__file__).resolve().parent
XML_CONFIG: Path = current_dir / Path("test_configurations/good_xml_config.xml")


test_xpath_1: str = "system[1]/security[1]/aaa[1]/local-profiles[2]/profile[5]/entry[30]/entry-id[110]/"
xpath_1_out: str = "ns:system[1]/ns:security[1]/ns:aaa[1]/ns:local-profiles[2]/ns:profile[5]/ns:entry[30]/ns:entry-id[110]"

test_xpath_2: str = "system/security/aaa/local-profiles/profile/entry/entry-id"
test_xpath_3: str = "system/security/aaa/local-profiles/profile/entry/entry-id/"
xpath_2_3_out: str = "ns:system/ns:security/ns:aaa/ns:local-profiles/ns:profile/ns:entry/ns:entry-id"



@pytest.mark.parametrize("input_x_path, expected_result", [
        (test_xpath_1, xpath_1_out),
        (test_xpath_2, xpath_2_3_out),
        (test_xpath_3, xpath_2_3_out),
])
def test_prepend_namespace(input_x_path, expected_result):
        test_xml_root = XMLRoot(XML_CONFIG).get_xml_root()
        test_config = ConfigHandler(test_xml_root)
        result = test_config.prepend_namespace(input_x_path)
        assert result == expected_result
