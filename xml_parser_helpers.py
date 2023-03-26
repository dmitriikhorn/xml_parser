import sys
from pathlib import Path
import logging
from logging import Logger, StreamHandler, Formatter


def read_file_content(filename: Path) -> str:
    """
    Open and read file content
    :param filename: Filename with path
    :return: Raw content of the file
    """
    if not filename.is_file():
        raise FileNotFoundError(f'Specified file "{filename}" is not found')
    return filename.open().read()


def create_file_log(end_file_name: str) -> str:
    """
    Create a log file with subdir "logs" if not existed
    :param end_file_name: Name of a log file
    :return: Canonical path to a log file
    """
    log_dir: Path = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    file_path = log_dir / end_file_name
    return str(file_path)


# def substitute_namespaces(self, element_tag: str) -> str:
#     """
#     Replace namespaces in a tag value returned by LXML with project NSes
#     For example: '{urn:nokia.com:sros:ns:yang:sr:conf}profile' ==> 'ns:profile'
#     :param element_tag: Element Tag value
#     :return: Element tag with replaced NS
#     """
#     for ns_k, ns_v in self.inverse_namespace_map.items():
#         if ns_k in element_tag:
#             return element_tag.replace(ns_k, f"{ns_v}:")
#     return element_tag

"""
Set up a Logger for this module:
INFO and above messages thrown to the console 
WARNING and above messages thrown to the file 
"""
xml_audit_logger: Logger = logging.getLogger('XMLAudit')
xml_audit_logger.setLevel(logging.DEBUG)

stream_handler: StreamHandler = StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
stream_format: Formatter = Formatter('%(name)s - %(levelname)s - %(message)s')
stream_handler.setFormatter(stream_format)

log_file: str = create_file_log('execution_logs.log')
file_handler: StreamHandler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_format: Formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_format)

xml_audit_logger.addHandler(stream_handler)
xml_audit_logger.addHandler(file_handler)
