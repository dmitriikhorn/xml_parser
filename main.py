from fastapi import FastAPI, HTTPException
from config_handler import XpathConstructor, XMLRoot, ConfigHandler
from pathlib import Path
from xml_parser_exceptions import XmlConfigurationLoadError
import xml_parser_dc as dc
from lxml.etree import _ElementTree


# To start an app:
# uvicorn main:xml_parser_app --port 58000 --reload
xml_parser_app = FastAPI()


def run_query_to_device(xml_query: list, device_name: str) -> list[list[dc.ResultItem]]:
    """
    Process API call as a query to particular device
    :param xml_query: query to the XML config
    :param device_name: Hostname of a device
    :return: Response to the query as a list of ResultItem dataclasses
    """
    device_cfg_location: Path = Path(f"configurations/{device_name}")
    adopted_x_path: list[dc.PathElement] = XpathConstructor(xml_query).convert_xpath_to_dataclass()
    xml_root: _ElementTree = XMLRoot(device_cfg_location).get_xml_root()
    parsed_configuration = ConfigHandler(xml_root)
    return parsed_configuration.process_query_pipeline(adopted_x_path)


@xml_parser_app.post("/xml_parser/")
def run_query_route(query_data: dict):
    items = dict()
    xpath: list = query_data.get("xpath")
    device_list: list = query_data.get("device_list")

    if not xpath:
        raise HTTPException(status_code=404, detail=f'Input XML query is absent')
    if not device_list:
        raise HTTPException(status_code=404, detail=f'Input list of devices is empty')

    for device_name in device_list:
        try:
            items[device_name] = run_query_to_device(xpath, device_name)
        except XmlConfigurationLoadError:
            raise HTTPException(status_code=404, detail=f'Configuration of the device "{device_name}" is corrupt or '
                                                        f'could not be found')
    if not any(items.values()):
        raise HTTPException(status_code=404, detail=f'Nothing is found in the selected configurations to the request')
    return items
