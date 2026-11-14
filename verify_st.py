"""Regenerate the three ST examples and compare them with TCT reference output."""

from argparse import ArgumentParser
from difflib import unified_diff
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory


PROJECT = Path(__file__).resolve().parent
EXAMPLES = {
    "Small_factory.py": "Small_factory.st",
    "Assembly_line.py": "Assembly_line.st",
    "Transfer_line.py": "transfer_line.st",
}
LEGACY_MODULE = "STSupervisorTCT.py"
LEGACY_INTERSECTION = "intersect = set([actuators[act].split(':')[0] for act in intersect])"
ORDERED_INTERSECTION = "intersect = sorted({actuators[act].split(':')[0] for act in intersect})"

RUN_LEGACY = """
import runpy
import sys
import STSupervisorTCT

def skip_plotting(*args, **kwargs):
    pass

STSupervisorTCT.process.generate_image = skip_plotting
STSupervisorTCT.process.plot_automatas = skip_plotting
runpy.run_path(sys.argv[1], run_name="__main__")
"""


def run_python(arguments, cwd, env):
    command = [sys.executable, "-B", "-X", "utf8", *arguments]
    result = subprocess.run(
        command, cwd=cwd, env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=90,
    )
    if result.returncode:
        detail = (result.stdout + result.stderr).strip()
        raise RuntimeError(f"Failed to run {arguments[-1]}:\n{detail}")


def generate_legacy(source, work, env):
    work.mkdir()
    for script in EXAMPLES:
        shutil.copyfile(source / script, work / script)
    original = (source / LEGACY_MODULE).read_text(encoding="utf-8")
    if original.count(LEGACY_INTERSECTION) != 1:
        raise ValueError("The legacy emitter does not match the expected intersection implementation.")
    # Normalize the unordered signal iteration in the temporary reference copy.
    ordered = original.replace(LEGACY_INTERSECTION, ORDERED_INTERSECTION)
    (work / LEGACY_MODULE).write_text(ordered, encoding="utf-8")
    legacy_env = dict(env, MPLBACKEND="Agg")
    for candidate in (source / "venv" / "Lib" / "site-packages",
                      source / ".venv" / "Lib" / "site-packages"):
        if candidate.is_dir():
            paths = [str(candidate)]
            if legacy_env.get("PYTHONPATH"):
                paths.append(legacy_env["PYTHONPATH"])
            legacy_env["PYTHONPATH"] = os.pathsep.join(paths)
            break
    for script in EXAMPLES:
        run_python(["-c", RUN_LEGACY, script], work, legacy_env)
    return work / "ST_Generated"


def compare(reference, generated, show_diff):
    mismatches = 0
    for filename in EXAMPLES.values():
        original = (reference / filename).read_text(encoding="utf-8")
        updated = (generated / filename).read_text(encoding="utf-8")
        if original == updated:
            print(f"MATCH {filename} ({len(updated.splitlines())} lines)")
            continue
        mismatches += 1
        print(f"DIFFERENT {filename} ({len(original.splitlines())} TCT lines, "
              f"{len(updated.splitlines())} DESlab lines)")
        if show_diff:
            sys.stdout.writelines(unified_diff(
                original.splitlines(keepends=True), updated.splitlines(keepends=True),
                fromfile=f"TCT/{filename}", tofile=f"DESlab/{filename}",
            ))
    return mismatches


def main():
    parser = ArgumentParser(description=__doc__)
    reference = parser.add_mutually_exclusive_group(required=True)
    reference.add_argument("--legacy-repo", type=Path, help="Checkout used to regenerate the TCT reference")
    reference.add_argument("--reference-dir", type=Path, help="Directory of pre-generated TCT ST files")
    parser.add_argument("--diff", action="store_true", help="Print a unified diff for each mismatch")
    args = parser.parse_args()

    env = dict(os.environ, PYTHONHASHSEED="0")
    try:
        with TemporaryDirectory(prefix="deslab-st-") as temp:
            work = Path(temp)
            original = (generate_legacy(args.legacy_repo.resolve(), work / "legacy", env)
                        if args.legacy_repo else args.reference_dir.resolve())
            updated = work / "generated"
            for script in EXAMPLES:
                run_python([str(PROJECT / script), "--output-dir", str(updated)], PROJECT, env)
            return int(compare(original, updated, args.diff) > 0)
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        parser.exit(2, f"Verification failed: {error}\n")


if __name__ == "__main__":
    sys.exit(main())
