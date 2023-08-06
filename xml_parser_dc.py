from dataclasses import dataclass, field
from typing import Any, Optional
import pydantic
from pydantic import BaseModel
from xml_parser_exceptions import IncorrectXmlParserApiRequest


@dataclass
class FilterElement:
    """
    For example:
    1. filter_path: user-profile-parent/user-profile-child
    /profile[re:match(user-profile-parent/user-profile-child, ".*")]
    2. filter_path: None (applied to the current root)
    /profile[re:match(text(), ".*")]
    """
    filter_path: str | None = None
    regexp: str | None = None
    indexed_query: str | None = None
    unindexed_path: str | None = None
    is_a_path: bool = True

    def __post_init__(self) -> None:
        if not self.filter_path:
            self.filter_path = "text()"
            self.is_a_path = False
        if not self.regexp:
            self.regexp = ".*"


@dataclass
class PathElement:
    name: str | None = None
    sibling_id: int | None = None
    filters: list[FilterElement] = field(default_factory=list)
    indexed_path: str | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise IncorrectXmlParserApiRequest(f"Name of the element in the XPATH is not provided")


class ResultItem(BaseModel):
    path_attribute: str = ""
    value: Any = None
