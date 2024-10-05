import pytest
from xml_parser_exceptions import XmlConfigurationLoadError
from config_handler import XMLRoot
from pathlib import Path
from lxml.etree import _ElementTree

current_dir: Path = Path(__file__).resolve().parent

rigged_config_1: Path = current_dir / Path("test_configurations/non_existing_config.xml")
rigged_config_2: Path = current_dir / Path("test_configurations/broken_xml_config.xml")
good_config_1: Path = current_dir / Path("test_configurations/good_xml_config.xml")


@pytest.mark.parametrize("input_xml_file", [rigged_config_1, rigged_config_2])
def test_get_xml_root_exceptions(input_xml_file):
    with pytest.raises(XmlConfigurationLoadError) as e_info:
        XMLRoot(input_xml_file).get_xml_root()


@pytest.mark.parametrize("input_xml_file", [good_config_1])
def test_get_xml_root(input_xml_file):
    xml_root = XMLRoot(input_xml_file).get_xml_root()
    assert isinstance(xml_root, _ElementTree)
