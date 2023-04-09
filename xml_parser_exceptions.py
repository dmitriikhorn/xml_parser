class XmlConfigurationLoadError(Exception):
    """
    Exception for handling:
    - configuration file I/O errors
    - wrong XML format
    """
    pass


class IncorrectXmlParserApiRequest(Exception):
    """
    Exception for handling incorrect API request to XML parser:
    - Empty query request
    - Empty list of nodes
    """
    pass
