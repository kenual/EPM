from typing import TypedDict


class UserProfile(TypedDict):
    url: str
    user: str
    pwd: str


class Application(UserProfile):
    app: str


class Database(Application):
    db: str


class Member(TypedDict):
    dimension: str
    name: str
    unique_name: str
