import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'runner'))
from comparator import REJECTION_MESSAGES, classify, create_judge, final_code
from receipt import REQUIRED, VERDICTS, validate, versions


class ComparatorTests(unittest.TestCase):
    def test_classification(self):
        for message in REJECTION_MESSAGES:
            with self.subTest(message=message):
                self.assertEqual(classify(1, 'error: ' + message + 'x'), 'REJECTED')
        self.assertEqual(classify(0, 'Your solution is okay!'), 'ACCEPTED')
        self.assertNotEqual(classify(1, 'Your solution is okay!'), 'ACCEPTED')
        self.assertEqual(classify(1, ''), 'TOOL_ERROR')
        self.assertEqual(classify(124, 'Your solution is okay!', True), 'TIMEOUT')

    def test_judge(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'judge'
            mathlib = Path(temp) / 'mathlib checkout'
            solution = Path(temp) / 'solution.lean'
            solution.write_text('-- source\n')
            create_judge(target, mathlib, versions()['LEAN_TOOLCHAIN'], solution)
            lake = (target / 'lakefile.toml').read_text()
            self.assertIn('name = "Challenge"', lake)
            self.assertIn('name = "Solution"', lake)
            self.assertIn(str(mathlib), lake)
            self.assertEqual((target / 'Solution.lean').read_text(), '-- source\n')
            config = json.loads((target / 'config.json').read_text())
            self.assertEqual(config['permitted_axioms'], versions()['PERMITTED_AXIOMS'].split())
            with self.assertRaises(FileExistsError):
                create_judge(target, mathlib, versions()['LEAN_TOOLCHAIN'])

    def test_codes_and_priority(self):
        self.assertEqual(set(VERDICTS), {0, 10, 11, 20, 21, 30, 31, 40})
        for code in (10, 20, 21, 30, 31):
            for status in ('ACCEPTED', 'REJECTED', 'TIMEOUT', 'TOOL_ERROR', 'SKIPPED'):
                self.assertEqual(final_code(code, status), code)
        for status, code in [('ACCEPTED', 0), ('REJECTED', 40), ('TIMEOUT', 11), ('TOOL_ERROR', 11), ('SKIPPED', 11)]:
            self.assertEqual(final_code(0, status), code)

    def test_receipt_comparator_required(self):
        data = {key: None for key in REQUIRED}
        data.update(steps={}, verdict_raw='COMPILED_CLEAN', comparator={'status': 'SKIPPED', 'rc': None, 'seconds': None, 'peak_rss_kb': None, 'log_tail': ''})
        validate(data)
        for key in list(data['comparator']):
            with self.subTest(key=key):
                copy = dict(data)
                copy['comparator'] = {k: v for k, v in data['comparator'].items() if k != key}
                with self.assertRaises(ValueError): validate(copy)

    def test_statement_matches_public_source(self):
        challenge = (ROOT / 'fixtures/public/challenge/Challenge.lean').read_text().splitlines()
        original = (ROOT / 'fixtures/public/core1/record-96308-v26.lean').read_text().splitlines()
        i = next(i for i, line in enumerate(challenge) if line.startswith('theorem '))
        self.assertEqual(challenge[i:i+2], [line.replace('_root_.', '') for line in original[127:129]])
