"""Append an import-only stub of the new names to the PRE-FIX manager in the comparison tree."""

path = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v678/cascor_e052ef8/src/api/lifecycle/manager.py"
stub = '''

# ---- VALIDATOR IMPORT-ONLY STUB (scratch comparison tree) ----
class _TruncatableGenerators:  # noqa: D101
    @staticmethod
    def derive(listing):
        raise NotImplementedError

    def reader(self, client_class, *, source, api_key):
        raise NotImplementedError

    def resolve(self, client_factory, *, source):
        raise NotImplementedError

    def reset(self):
        return None


_TRUNCATABLE_GENERATORS = _TruncatableGenerators()
_GENERATOR_LIST_TIMEOUT_SECONDS = 5
_GENERATOR_LIST_RETRIES = 0
'''
with open(path, encoding="utf-8") as fh:
    src = fh.read()
if "VALIDATOR IMPORT-ONLY STUB" not in src:
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(stub)
print("stubbed")
