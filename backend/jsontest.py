import json
from pathlib import Path
from typing import Collection

filepath = Path('./test.json').absolute()


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


process_json(data)
