from starlette.config import Config
from starlette.datastructures import Secret

try:
    Config = Config(".env")

except FileNotFoundError:
    Config = Config()

DATABASE_URL = Config("DATABASE_URL", cast=Secret)
