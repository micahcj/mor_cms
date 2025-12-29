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
    def help_print(val):
        print(indent*'\t', val)
    for item in data:
        if isinstance(item, list):
            process_json(item, indent+1)
        else:
            help_print(item)


process_json(data)
