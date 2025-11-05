import os
from pathlib import Path

import yaml


def read_yaml(key, yaml_path):
    with open(f"{str(Path.cwd())}{yaml_path}", encoding="utf-8") as f:
        value = yaml.load(stream=f, Loader=yaml.FullLoader)
        return value[key]


def read_yaml_special(yaml_path):
    with open(f"{str(Path.cwd())}{yaml_path}", encoding="utf-8") as f:
        data = yaml.load(stream=f, Loader=yaml.FullLoader)
        return data


def write_yaml(data, yaml_path):
    with open(f"{str(Path.cwd())}{yaml_path}", encoding="utf-8", mode="a") as f:
        yaml.dump(data, stream=f, allow_unicode=True)
        print("写入了")


def clear_yaml(yaml_path):
    with open(f"{str(Path.cwd())}{yaml_path}", encoding="utf-8", mode="w") as f:
        f.truncate()


def flush_yaml(yaml_path):
    with open(f"{str(Path.cwd())}{yaml_path}", 'r') as file:
        file.flush()


if __name__ == '__main__':
    print(Path.cwd())
    print(type(Path.cwd()))
