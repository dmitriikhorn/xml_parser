from dataclasses import dataclass, field
from typing import Any, Optional
import pydantic
from pydantic import BaseModel,root_validator, validator
from xml_parser_exceptions import IncorrectXmlParserApiRequest


class FilterElement(BaseModel):
    """
    For example:
    1. filter_path: user-profile-parent/user-profile-child
    /profile[re:match(user-profile-parent/user-profile-child, "regex")]
    2. filter_path: (applied to the current root) /profile[re:match(text(), ".*")]
    """
    filter_path: str
    regexp: str
    is_a_path: bool = True
    indexed_query: str | None
    unindexed_path: str | None

    def __init__(self, **values: dict[str]):
        super().__init__(**values)
        if not values.get("filter_path"):
            self.is_a_path = False

    @validator("regexp")
    @classmethod
    def validate_regexp(cls, value: str) -> str:
        return value or ".*"

    @validator("filter_path")
    @classmethod
    def validate_filter_path(cls, value: str) -> str:
        return value or "text()"


class PathElement(BaseModel):
    name: str
    sibling_id: int | None
    filters: list[FilterElement] = list()
    indexed_path: str | None

    @validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str:
        if not value:
            raise IncorrectXmlParserApiRequest(f"Name of the element in the XPATH is not provided")
        return value


class ResultItem(BaseModel):
    path_attribute: str = ""
    value: Any = None

