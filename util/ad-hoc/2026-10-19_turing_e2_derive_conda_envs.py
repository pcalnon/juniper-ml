"""
Derive turing's osx-64 conda env specs (plan task E2) from the three repos' own Linux env specs.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-19
Status: ad-hoc — one-off (turing bring-up task E2: per-repo conda envs, decision D8)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (D8, Arc E row E2, gate G-ENV);
         conf/hosts/turing/conda-envs/{JuniperCascor1,JuniperData,JuniperCanopy1}.yml, the output. Each file's
         header records its source sha, the rules, the relaxations and the solve.

Why:
  juniper-cascor and juniper-canopy ship `conda list --export` dumps from a linux-64 host, and juniper-data a YAML
  spec that names Linux-only packages and the nvidia channel; none of them solves on osx-64. The port keeps every
  conda package at its Linux version (build string dropped), drops the Linux-only and CUDA packages, swaps PyPI
  torch for conda-forge pytorch (PyPI has no x86_64 macOS torch wheel after 2.2), moves the other =pypi_0 lines to
  a pip: section, and relaxes only the pins that have no osx-64 build or cannot co-solve with one. RELAXATIONS
  holds the 2026-10-19 decisions. A pin still missing on osx-64 is printed with its nearest versions and fails the
  run, so a re-run against newer Linux specs shows exactly what is left to decide.

Steps (WORK is any directory outside the repo):
  python3 -I util/ad-hoc/2026-10-19_turing_e2_derive_conda_envs.py --work WORK fetch
      gh api: each repo's main sha, and conf/conda_environment.yaml at it -> WORK/specs/
      /usr/bin/curl: conda-forge osx-64 + noarch repodata.json.zst -> WORK/repodata/
  /usr/local/miniforge3/bin/python3 -I util/ad-hoc/2026-10-19_turing_e2_derive_conda_envs.py --work WORK derive
      Needs the conda base interpreter, for conda.models.version and zstandard. Classifies every source line,
      checks it against osx-64 + noarch for CPython 3.14, and writes the spec body to WORK/derived/<Env>.yml
      (conda specs sorted, pip: block last; the header is written by hand).
  /usr/local/miniforge3/bin/python3 -I util/ad-hoc/2026-10-19_turing_e2_derive_conda_envs.py --work WORK check
      Unpacks the repodata into a metadata-only file:// channel and runs `mamba env create --dry-run` on each
      derived spec, pip: block removed. It only solves: the channel holds no packages, so nothing can install.

Exit 0 = the step succeeded (derive: no unresolved pin; check: every spec solves); 1 otherwise.
"""

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

REPOS = {"cascor": ("juniper-cascor", "JuniperCascor1"), "data": ("juniper-data", "JuniperData"), "canopy": ("juniper-canopy", "JuniperCanopy1")}
SPEC_PATH = "conf/conda_environment.yaml"
REPODATA_URL = "https://conda.anaconda.org/conda-forge/{subdir}/repodata.json.zst"
PY_FULL = "3.14.2"  # the Linux exports' python: a build is usable if it installs beside it
MAMBA = "/usr/local/miniforge3/bin/mamba"

# Linux runtime and toolchain. c-compiler / cxx-compiler are what install the gcc set on Linux; on macOS they
# would bring a clang toolchain the env never had.
LINUX_ONLY = [
    "_libgcc_mutex", "_openmp_mutex", "ld_impl_linux-64", "libgcc", "libgcc-ng", "libgomp", "libstdcxx", "libstdcxx-ng",
    "libuuid", "alsa-lib", "attr", "libcap", "keyutils", "binutils", "binutils_impl_linux-64", "binutils_linux-64",
    "gcc", "gcc_impl_linux-64", "gcc_linux-64", "gxx", "gxx_impl_linux-64", "gxx_linux-64", "conda-gcc-specs",
    "libsanitizer", "sysroot_linux-64", "kernel-headers_linux-64", "*_linux-64", "c-compiler", "cxx-compiler",
]
CUDA = [
    "cuda", "cuda-*", "nvidia-*", "triton", "libcublas*", "libcufft*", "libcufile*", "libcurand*", "libcusolver*",
    "libcusparse*", "libnpp*", "libnvfatbin*", "libnvjitlink*", "libnvjpeg*", "libnvptxcompiler*", "nsight-*", "gds-tools",
]
# The 2026-10-19 decisions; each one's reason is in the env file's header. "pip:<name>" is a pip-section pin.
RELAXATIONS = {
    "JuniperCascor1": {"pytorch": "2.10.0", "libtorch": "2.10.0", "mkl": "2023.2.0", "tbb": "2021.13.0", "libblas": "3.9.0", "libcblas": "3.9.0", "liblapack": "3.9.0"},
    "JuniperData": {},
    "JuniperCanopy1": {"pytorch": "2.10.0", "xkeyboard-config": "2.47", "xorg-libx11": "1.8.13", "pip:juniper-data": "0.4.2"},
}


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def fetch(work):
    (work / "specs").mkdir(parents=True, exist_ok=True)
    (work / "repodata").mkdir(parents=True, exist_ok=True)
    for key, (repo, _env) in REPOS.items():
        sha = sh(["gh", "api", f"repos/pcalnon/{repo}/commits/main", "--jq", ".sha"]).strip()
        body = sh(["gh", "api", "-H", "Accept: application/vnd.github.raw+json", f"repos/pcalnon/{repo}/contents/{SPEC_PATH}?ref={sha}"])
        with open(work / "specs" / f"{key}.yaml", "w") as fh:
            fh.write(body)
        with open(work / "specs" / f"{key}.sha", "w") as fh:
            fh.write(sha + "\n")
        print(f"{repo}: main {sha}")
    for subdir in ("osx-64", "noarch"):
        dest = work / "repodata" / f"{subdir}.repodata.json.zst"
        subprocess.run(["/usr/bin/curl", "-sS", "--fail", "--max-time", "600", "-o", str(dest), REPODATA_URL.format(subdir=subdir)], check=True)
        print(f"conda-forge {subdir}: {dest.stat().st_size} bytes")
    return 0


def load_repodata(work):
    import zstandard  # conda base interpreter only

    index = {}
    for subdir in ("osx-64", "noarch"):
        with open(work / "repodata" / f"{subdir}.repodata.json.zst", "rb") as fh:
            data = json.loads(zstandard.ZstdDecompressor().decompress(fh.read(), max_output_size=2_000_000_000))
        for section in ("packages", "packages.conda"):
            for rec in data.get(section, {}).values():
                index.setdefault(rec["name"], {}).setdefault(rec["version"], []).append(dict(rec, subdir=subdir))
    return index


def usable(rec, version_spec):
    """A build installs beside CPython PY_FULL (GIL): noarch, no python dependency, or one admitting PY_FULL."""
    if rec["subdir"] == "noarch":
        return True
    for dep in rec.get("depends", []):
        parts = dep.split()
        if parts[0] in ("python", "python_abi") and len(parts) > 1:
            if not version_spec(parts[1]).match(PY_FULL):
                return False
            if parts[0] == "python_abi" and len(parts) > 2 and parts[2].endswith("t"):
                return False
    return True


def matches(name, patterns):
    return any(fnmatch.fnmatchcase(name, p) for p in patterns)


def derive(work):
    from conda.models.version import VersionOrder, VersionSpec  # conda base interpreter only

    index = load_repodata(work)

    def versions(name):
        vs = [v for v, recs in index.get(name, {}).items() if any(usable(r, VersionSpec) for r in recs)]
        return sorted(vs, key=VersionOrder)

    def resolve(env, name, version, relax_key, unresolved):
        relaxed = RELAXATIONS[env].get(relax_key)
        if relaxed:
            if relax_key.startswith("pip:") or relaxed in versions(name):
                print(f"  RELAX  {relax_key} {version} -> {relaxed}")
                return relaxed
            unresolved.append(f"{relax_key}: relaxation {relaxed} is not on osx-64")
            return version
        if relax_key.startswith("pip:") or version in versions(name):
            return version
        lower = [v for v in versions(name) if VersionOrder(v) < VersionOrder(version)]
        higher = [v for v in versions(name) if VersionOrder(v) > VersionOrder(version)]
        unresolved.append(f"{name}={version}: not on osx-64; nearest lower {lower[-1] if lower else None}, higher {higher[0] if higher else None}")
        return version

    failed = 0
    (work / "derived").mkdir(parents=True, exist_ok=True)
    for key, (repo, env) in REPOS.items():
        with open(work / "specs" / f"{key}.yaml") as fh:
            text = fh.read()
        print(f"== {env} (from {repo} {SPEC_PATH})")
        conda, pip, unresolved = {}, {}, []
        if "# platform: linux-64" in text:
            for line in text.splitlines():
                if not line.strip() or line.startswith("#"):
                    continue
                name, version, build = line.strip().split("=")
                if matches(name, CUDA):
                    print(f"  DROP   {name} (CUDA)")
                elif build == "pypi_0" and name == "torch":
                    print(f"  SWAP   torch {version} (PyPI) -> conda-forge pytorch")
                    conda["pytorch"] = resolve(env, "pytorch", version, "pytorch", unresolved)
                elif build == "pypi_0":
                    pip[name] = resolve(env, name, version, f"pip:{name}", unresolved)
                elif matches(name, LINUX_ONLY):
                    print(f"  DROP   {name} (Linux runtime/toolchain)")
                elif not versions(name):
                    print(f"  DROP   {name} (no osx-64 build at any version)")
                else:
                    conda[name] = resolve(env, name, version, name, unresolved)
        else:  # a hand-kept YAML spec: keep the names and any pin it carries
            for dep in re.findall(r"(?m)^  - ([^\s#]+)", text.split("dependencies:", 1)[1]):
                name, _, version = dep.partition("=")
                if name in conda:
                    print(f"  DEDUP  {name}")
                elif matches(name, CUDA) or matches(name, LINUX_ONLY):
                    print(f"  DROP   {name} (Linux-only or CUDA)")
                elif not versions(name):
                    print(f"  DROP   {name} (no osx-64 build at any version)")
                else:
                    conda[name] = version
        for problem in unresolved:
            print(f"  UNRESOLVED {problem}")
        failed |= bool(unresolved)
        body = [f"name: {env}", "channels:", "  - conda-forge", "dependencies:"]
        body += [f"  - {n}={v}" if v else f"  - {n}" for n, v in sorted(conda.items(), key=lambda kv: kv[0].lower())]
        if pip:
            body += ["  - pip:"] + [f"      - {n}=={v}" for n, v in sorted(pip.items(), key=lambda kv: kv[0].lower())]
        with open(work / "derived" / f"{env}.yml", "w") as fh:
            fh.write("\n".join(body) + "\n")
        print(f"  -> {work / 'derived' / (env + '.yml')}: {len(conda)} conda, {len(pip)} pip")
    return 1 if failed else 0


def check(work):
    import zstandard  # conda base interpreter only

    channel = work / "localchannel"
    for subdir in ("osx-64", "noarch"):
        (channel / subdir).mkdir(parents=True, exist_ok=True)
        with open(work / "repodata" / f"{subdir}.repodata.json.zst", "rb") as src, open(channel / subdir / "repodata.json", "wb") as dst:
            dst.write(zstandard.ZstdDecompressor().decompress(src.read(), max_output_size=2_000_000_000))
    failed = 0
    for _key, (_repo, env) in REPOS.items():
        with open(work / "derived" / f"{env}.yml") as fh:
            text = fh.read()
        text = text.replace("  - conda-forge\n", f"  - file://{channel}\n", 1)
        text = re.sub(r"(?ms)^  - pip:\n(      - [^\n]+\n)+", "", text)
        offline = work / "derived" / f"{env}.offline.yml"
        with open(offline, "w") as fh:
            fh.write(text)
        result = subprocess.run([MAMBA, "env", "create", "-f", str(offline), "--override-channels", "-c", f"file://{channel}", "--dry-run"], capture_output=True, text=True)
        installs = re.search(r"Install:\s+(\d+) packages", result.stdout)
        print(f"{env}: exit {result.returncode}, {installs.group(1) if installs else '?'} packages")
        if result.returncode:
            print("\n".join(line for line in (result.stdout + result.stderr).splitlines() if "invalid url" not in line)[-2000:])
            failed = 1
    return failed


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("step", choices=("fetch", "derive", "check"))
    args = parser.parse_args()
    return {"fetch": fetch, "derive": derive, "check": check}[args.step](args.work.resolve())


if __name__ == "__main__":
    sys.exit(main())
