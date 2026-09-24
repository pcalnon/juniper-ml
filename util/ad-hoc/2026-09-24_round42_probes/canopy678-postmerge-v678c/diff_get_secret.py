"""Differential check: get_secret at 9cdfcad4 (before #678) vs 05f2dfc2 (after), same inputs.

Loads both secrets_util.py files by path as separate modules and runs them over a matrix of
file-var / env-var states, comparing the returned value or the exception (type + message), and
whether anything was logged. Also checks resolve_secret's (value, source) for the same inputs.
"""

import importlib.util
import itertools
import logging
import os
import stat
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def load(tree, name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, tree, "src", "secrets_util.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


old = load("9cdfcad4", "secrets_util_old")
new = load("05f2dfc2", "secrets_util_new")

tmp = tempfile.mkdtemp(dir=HERE)


def mk(name, content, mode=None, binary=False):
    p = os.path.join(tmp, name)
    with open(p, "wb" if binary else "w") as fh:
        fh.write(content)
    if mode is not None:
        os.chmod(p, mode)
    return p


FILES = {
    "unset": None,
    "empty-var": "",
    "missing-path": os.path.join(tmp, "absent"),
    "directory": tmp,
    "real": mk("real", "file-key\n"),
    "padded": mk("padded", "  file-key \t\n"),
    "blank": mk("blank", " \t \n"),
    "empty-file": mk("empty", ""),
    "multiline": mk("multi", "a\nb\n"),
    "unicode": mk("uni", "kéy- x\n"),
    "nbsp-only": mk("nbsp", " \n"),
    "non-utf8": mk("bin", b"\xff\xfekey", binary=True),
    "unreadable": mk("unread", "secret-key\n", mode=0),
    "symlink": None,  # filled below
}
link = os.path.join(tmp, "link")
os.symlink(FILES["real"], link)
FILES["symlink"] = link
dangling = os.path.join(tmp, "dangling")
os.symlink(os.path.join(tmp, "nowhere"), dangling)
FILES["dangling-symlink"] = dangling

ENVS = {"unset": None, "empty": "", "blank": " \t ", "real": "env-key", "padded": "  env-key  ", "nbsp": " "}

records = []


class H(logging.Handler):
    def emit(self, r):
        records.append(r)


logging.getLogger().addHandler(H())
logging.getLogger().setLevel(logging.DEBUG)


def call(fn, *a):
    try:
        return ("ok", fn(*a))
    except Exception as exc:  # noqa: BLE001
        return ("exc", type(exc).__name__, str(exc))


mismatch = 0
n = 0
for (fk, fv), (ek, ev), custom in itertools.product(FILES.items(), ENVS.items(), (False, True)):
    fvar = "CUSTOM_FILE_VAR" if custom else "PROBE_SECRET_FILE"
    for v in ("PROBE_SECRET_FILE", "CUSTOM_FILE_VAR", "PROBE_SECRET"):
        os.environ.pop(v, None)
    if fv is not None:
        os.environ[fvar] = fv
    if ev is not None:
        os.environ["PROBE_SECRET"] = ev
    args = ("PROBE_SECRET", "CUSTOM_FILE_VAR") if custom else ("PROBE_SECRET",)
    a = call(old.get_secret, *args)
    b = call(new.get_secret, *args)
    r = call(new.resolve_secret, *args)
    n += 1
    if a != b:
        mismatch += 1
        print("MISMATCH", fk, ek, custom, a, b)
    # resolve_secret's value must equal get_secret's, and the source must be the var that supplied it
    if r[0] == "ok":
        val, src = r[1]
        if (b[0] == "ok" and val != b[1]) or (val is None) != (src is None):
            print("RESOLVE INCONSISTENT", fk, ek, custom, r, b)
    elif r != b:
        print("RESOLVE EXC DIFFERS", fk, ek, custom, r, b)
    if fk in ("unreadable", "non-utf8") and ek == "real" and not custom:
        print(f"  sample [{fk}] old={a} new={b}")
print(f"{n} cases, {mismatch} old/new mismatches, {len(records)} log records emitted by either version")
os.chmod(FILES["unreadable"], stat.S_IRUSR | stat.S_IWUSR)
