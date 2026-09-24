"""Print where canopy's top-level modules resolve from, to prove the scratch tree is under test."""

import sys

import backend
import communication
import frontend
import juniper_canopy
import logger
import secrets_util
import security

for m in (backend, frontend, logger, communication, juniper_canopy, security, secrets_util):
    print(m.__name__, getattr(m, "__file__", None))
print("sys.path[:4]", sys.path[:4])
