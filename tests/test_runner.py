import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runner'))
from receipt import REQUIRED, VERDICTS, validate
from scan import scan
from token_count import clean, LEXER


class ScanTests(unittest.TestCase):
    def test_sorry_and_admit(self):
        hits, decls = scan('theorem x : True := by sorry\ntheorem y : True := by admit\naxiom cheat : False')
        self.assertEqual([x['word'] for x in hits], ['sorry', 'admit'])
        self.assertEqual(decls, [{'name': 'cheat', 'line': 3}])

    def test_comments_strings_nested(self):
        source = '/- sorry /- admit axiom fake : False -/ still sorry -/\n-- admit\ndef s := "sorry \\\" admit"\n'
        self.assertEqual(scan(source), ([], []))

    def test_word_boundaries(self):
        self.assertEqual(scan('sorryish admitted sorry\'')[0], [])


class TokenTests(unittest.TestCase):
    def test_hand_count(self):
        # After removing import and comment: "\ndef x := 1 + 2\n".
        # Lexer: def | x | := | 1 | + | 2 = 6; 17 characters including spaces.
        stripped = clean('import Foo\ndef x := 1 + 2 -- note\n')
        self.assertEqual(stripped, '\ndef x := 1 + 2 \n')
        self.assertEqual(len(LEXER.findall(stripped)), 6)
        self.assertEqual(len(stripped), 17)


class ReceiptTests(unittest.TestCase):
    def test_every_required_field(self):
        data = {key: None for key in REQUIRED}
        data['steps'] = {'compile': {'rc': 0, 'seconds': 1}}
        data['verdict_raw'] = 'COMPILED_CLEAN'
        validate(data)
        for key in REQUIRED:
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate({k: v for k, v in data.items() if k != key})

    def test_step_fields(self):
        data = {key: None for key in REQUIRED}
        data.update(steps={'compile': {'rc': 0}}, verdict_raw='COMPILED_CLEAN')
        with self.assertRaises(ValueError): validate(data)

    def test_exit_verdict_mapping(self):
        self.assertEqual(VERDICTS, {0: 'COMPILED_CLEAN', 10: 'ENV_ERROR', 20: 'COMPILE_ERROR',
                                    21: 'TIMEOUT', 30: 'AXIOM_EXTRA', 31: 'SORRY_FOUND'})


if __name__ == '__main__': unittest.main()
