"""Lane B: confirm juniper_data resolves to the extracted tree and print library versions."""

import sys

import fastapi
import pydantic
import starlette

import juniper_data

print(juniper_data.__file__, juniper_data.__version__)
print("fastapi", fastapi.__version__, "starlette", starlette.__version__, "pydantic", pydantic.__version__)
print(sys.version)
