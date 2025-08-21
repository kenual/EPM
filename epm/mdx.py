from typing import List, TypedDict
from pydantic import BaseModel

from epm.data_types import Member


class MemberRange(TypedDict):
    start_member_name: Member
    end_member_name: Member


class SetFunction(BaseModel):
    function_name: str


class Set(TypedDict):
    members: MemberRange | List[str] | SetFunction


def member_range_MDX_expression(member_range: MemberRange) -> str:
    """
    Generate an MDX member range expression for Essbase.

    Args:
        member_range (MemberRange): A dictionary with keys 'start_member_name' and 'end_member_name'.

    Returns:
        str: An MDX expression representing the member range.
    """
    return f"MemberRange({member_range['start_member_name']['unique_name']}, {member_range['end_member_name']['unique_name']})"


def set_MDX_expression(set_: Set) -> str:
    """
    Generate an MDX set expression for Essbase.

    Args:
        set_ (Set): A dictionary with a 'members' key. 'members' can be a MemberRange, list of member names, or a SetFunction.

    Returns:
        str: An MDX expression string representing the set.
    """
    if isinstance(set_['members'], MemberRange):
        return member_range_MDX_expression(set_['members'])
    elif isinstance(set_['members'], list):
        return "{" + ", ".join(set_['members']) + "}"
    elif isinstance(set_['members'], SetFunction):
        return f"{set_['members'].function_name}()"
    else:
        raise ValueError("Invalid members type in Set")
