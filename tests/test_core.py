import unittest

from non_decimal_integer_literal_parser import InvalidLiteralError, parse_int


class ParseIntTests(unittest.TestCase):
    def test_hex_basic(self):
        self.assertEqual(parse_int("0xFF"), 255)
        self.assertEqual(parse_int("0Xff"), 255)
        self.assertEqual(parse_int("0x0"), 0)

    def test_binary_basic(self):
        self.assertEqual(parse_int("0b1010"), 10)
        self.assertEqual(parse_int("0B1111"), 15)

    def test_octal_basic(self):
        self.assertEqual(parse_int("0o17"), 15)
        self.assertEqual(parse_int("0O777"), 511)

    def test_signs(self):
        self.assertEqual(parse_int("+0x10"), 16)
        self.assertEqual(parse_int("-0x10"), -16)
        self.assertEqual(parse_int("-0b1"), -1)

    def test_suffixes_are_accepted_and_ignored(self):
        self.assertEqual(parse_int("0xFFu"), 255)
        self.assertEqual(parse_int("0xFFU"), 255)
        self.assertEqual(parse_int("0xFFl"), 255)
        self.assertEqual(parse_int("0xFFL"), 255)
        self.assertEqual(parse_int("0xFFll"), 255)
        self.assertEqual(parse_int("0xFFLL"), 255)
        self.assertEqual(parse_int("0xFFul"), 255)
        self.assertEqual(parse_int("0xFFlu"), 255)
        self.assertEqual(parse_int("0xFFull"), 255)
        self.assertEqual(parse_int("0xFFLLU"), 255)

    def test_large_values(self):
        # Python ints are arbitrary precision; make sure we do not clip.
        self.assertEqual(parse_int("0xFFFFFFFFFFFFFFFF"), 2**64 - 1)
        self.assertEqual(parse_int("0b" + "1" * 100), 2**100 - 1)

    def test_empty_and_sign_only(self):
        with self.assertRaises(InvalidLiteralError):
            parse_int("")
        with self.assertRaises(InvalidLiteralError):
            parse_int("-")
        with self.assertRaises(InvalidLiteralError):
            parse_int("+")

    def test_missing_marker(self):
        with self.assertRaises(InvalidLiteralError):
            parse_int("123")
        with self.assertRaises(InvalidLiteralError):
            parse_int("FF")

    def test_marker_without_digits(self):
        with self.assertRaises(InvalidLiteralError):
            parse_int("0x")
        with self.assertRaises(InvalidLiteralError):
            parse_int("0b")
        with self.assertRaises(InvalidLiteralError):
            parse_int("0o")

    def test_invalid_digit_for_base(self):
        with self.assertRaises(InvalidLiteralError):
            parse_int("0b2")
        with self.assertRaises(InvalidLiteralError):
            parse_int("0o8")
        with self.assertRaises(InvalidLiteralError):
            parse_int("0xG")

    def test_whitespace_is_not_stripped(self):
        with self.assertRaises(InvalidLiteralError):
            parse_int(" 0xFF")
        with self.assertRaises(InvalidLiteralError):
            parse_int("0xFF ")

    def test_underscores_are_rejected(self):
        # Python allows 0xFF_FF; this parser intentionally does not, so
        # the grammar stays identical to C's pre-C23 rules.
        with self.assertRaises(InvalidLiteralError):
            parse_int("0xFF_FF")

    def test_non_string_input(self):
        with self.assertRaises(TypeError):
            parse_int(255)  # type: ignore[arg-type]

    def test_error_is_value_error(self):
        # Callers that catch ValueError should keep working.
        with self.assertRaises(ValueError):
            parse_int("0xZZ")

    def test_suffix_only(self):
        with self.assertRaises(InvalidLiteralError):
            parse_int("0xu")

    def test_double_sign_is_rejected(self):
        with self.assertRaises(InvalidLiteralError):
            parse_int("--0x1")


if __name__ == "__main__":
    unittest.main()
