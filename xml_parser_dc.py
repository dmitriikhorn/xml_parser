from dataclasses import dataclass, field
from typing import Any
from pydantic import BaseModel


@dataclass
class FilterElement:
    """
    For example:
    1. filter_path: user-profile-parent/user-profile-child
    /profile[re:match(user-profile-parent/user-profile-child, ".*")]
    2. filter_path: None (applied to the current root)
    /profile[re:match(text(), ".*")]
    """
    regexp: str = '.*'
    filter_path: str = None
    indexed_query: str = ""
    unindexed_path: str = ""


@dataclass
class PathElement:
    name: str = ''
    full_name: str = ''
    sibling_id: int = None
    filters: list[FilterElement] = field(default_factory=list)
    indexed_path: str = ''


class ResultItem(BaseModel):
    path_attribute: str = ''
    value: Any = None
