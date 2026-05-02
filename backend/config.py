from os import path

BASE_DIR = path.dirname(path.abspath(__file__))

DATA_PATH = path.join(BASE_DIR, "data", "schemes.json")
TOP_K = 3