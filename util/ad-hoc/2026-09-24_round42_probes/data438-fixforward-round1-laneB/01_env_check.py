"""Lane B (r42d): report interpreter and import origin."""

import sys
import sysconfig

import juniper_data

print(sys.version)
print(juniper_data.__file__)
print("Py_GIL_DISABLED", sysconfig.get_config_var("Py_GIL_DISABLED"), "gil enabled now", sys._is_gil_enabled())
