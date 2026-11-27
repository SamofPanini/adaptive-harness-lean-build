"""Comparator log classification and isolated Lake project creation."""
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent.parent
# Literal fragments, including distinct punctuation, from the pinned sources.
REJECTION_MESSAGES = (
    'Const not found in challenge \u0027',  # Comparator/Compare.lean:46
    'Const not found in solution \u0027',  # Comparator/Compare.lean:48
    'Const does not match between challenge and target \u0027',  # Comparator/Compare.lean:55,102
    'Const not found in challenge: \u0027',  # Comparator/Compare.lean:73,91
    'Const not found in solution: \u0027',  # Comparator/Compare.lean:76,94; Comparator/Axioms.lean:57,64
    "Challenge and solution constant kind don't match: '",  # Comparator/Compare.lean:82
    'Challenge and solution theorem statement do not match: \u0027',  # Comparator/Compare.lean:85
    'Challenge constant is not a definition: \u0027',  # Comparator/Compare.lean:97
    'Solution constant is not a definition: \u0027',  # Comparator/Compare.lean:99; Comparator/Axioms.lean:66
    'Constant not found in solution \u0027',  # Comparator/Axioms.lean:32,40
    'Illegal axiom detected: \u0027',  # Comparator/Axioms.lean:44
    'Solution constant is not a theorem: \u0027',  # Comparator/Axioms.lean:59
    'Lean default kernel rejects the solution',  # Main.lean:225
    'Quotient post-check rejects the solution',  # Main.lean:238
    'kernel rejected the solution',  # Main.lean:199
)


def classify(rc, log, timed_out=False):
    if timed_out:
        return 'TIMEOUT'
    if rc == 0 and 'Your solution is okay!' in log:
        return 'ACCEPTED'
    if any(message in log for message in REJECTION_MESSAGES):
        return 'REJECTED'
    return 'TOOL_ERROR'


def create_judge(target, mathlib, toolchain, solution=None):
    target = Path(target)
    target.mkdir(parents=True, exist_ok=False)
    # JSON escaping produces a TOML basic string for a filesystem path.
    (target / 'lakefile.toml').write_text(
        'name = "judge"\npackagesDir = ' + json.dumps(str(Path(mathlib).resolve() / '.lake/packages')) +
        '\n\n[[require]]\nname = "mathlib"\npath = ' + json.dumps(str(Path(mathlib).resolve())) +
        '\n\n[[lean_lib]]\nname = "Challenge"\n\n[[lean_lib]]\nname = "Solution"\n')
    (target / 'lean-toolchain').write_text(toolchain + '\n')
    challenge = ROOT / 'fixtures/public/challenge'
    shutil.copyfile(challenge / 'Challenge.lean', target / 'Challenge.lean')
    shutil.copyfile(challenge / 'comparator.json', target / 'config.json')
    if solution is not None:
        shutil.copyfile(solution, target / 'Solution.lean')
    return target


def final_code(original, status):
    if original != 0:
        return original
    return {'ACCEPTED': 0, 'REJECTED': 40}.get(status, 11)
