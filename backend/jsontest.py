from dataclasses import dataclass
import json
from pathlib import Path
from typing import Collection

from pydantic import BaseModel


def get_path(path: str) -> Path:
    return Path(path).absolute()


path = '/Users/micah/Documents/CodeMe/mor_cms/backend/test.json'
filepath = get_path(path)


def load_file(filepath=filepath):
    with open(filepath, 'r') as file:
        data = json.load(file)
    return data


data = load_file()
# print(*[x for x in data], sep='\n')


def process_json(data: list, indent=0):
    def tag(val):
        return f'<li>{val}</li>'

    def nest_init(val):
        return f'<ul>{val}</ul>'

    def help_print(val):
        print(indent*'\t', tag(val))
    for item in data:
        if isinstance(item, list):
            process_json(item, indent+1)
        else:
            if indent:
                print(indent*'\t', ('<ul>'))
            help_print(item)
            if indent:
                print(indent*'\t', ('</ul>'))


@dataclass
class ResultText:
    json: dict[str, str | list[str]]
    html: str


class ResultTextBase(BaseModel):
    json: dict[str, str | list[str]]
    html: str


if __name__ == "__main__":
    process_json(data)
    print(ResultText(**data))
    print(ResultTextBase(**data))

# functionally, contain every main in an li
