"""Apply the proposed conftest fix to the SCRATCH copy (cascor-full) only."""
p = "cascor-full/src/tests/conftest.py"
s = open(p, encoding="utf-8").read()
anchor = "import sysconfig\n"
fix = (
    "import sysconfig\n\n"
    "# Never let a test process initialise the REAL Sentry SDK. src/main.py runs sentry_sdk.init at\n"
    "# IMPORT time from JUNIPER_CASCOR_SENTRY_DSN / SENTRY_SDK_DSN, and test_cfg_03 imports main at\n"
    "# collection. Empty rather than deleted: main.py's load_dotenv() (override=False) cannot then\n"
    "# re-inject a DSN from a .env, and subprocess probes inherit the empty values.\n"
    'for _dsn_var in ("SENTRY_SDK_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "SENTRY_DSN"):\n'
    '    os.environ[_dsn_var] = ""\n'
)
assert s.count(anchor) == 1
if "_dsn_var" not in s:
    s = s.replace(anchor, fix, 1)
    open(p, "w", encoding="utf-8").write(s)
print("applied:", "_dsn_var" in open(p, encoding="utf-8").read())
