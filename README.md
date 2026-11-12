# non-decimal-integer-literal-parser

Parse C-style non-decimal integer literals (hex, binary, octal) with optional
sign and integer suffix into Python `int` values.

```python
from non_decimal_integer_literal_parser import parse_int, InvalidLiteralError

parse_int("0xFF")        # 255
parse_int("-0b1010")     # -10
parse_int("0o17u")       # 15
parse_int("0xFFull")     # 255

try:
    parse_int("0b2")
except InvalidLiteralError as exc:
    print(exc)  # invalid digit '2' at position 2 in '0b2'
```

## Why this exists

Python's built-in `int(text, 0)` accepts a lot more than C does: it allows
underscores as digit separators, it accepts a bare `0` as decimal zero, and it
raises a generic `ValueError` with no position information. If you are reading
literals out of C, C++, or Java source and want to reject anything the compiler
would reject, you need a parser with a narrower grammar.

The trade-off is deliberate: this library implements exactly the C literal
forms listed below and nothing else. It does not accept decimal literals, it
does not strip whitespace, and it does not accept underscore separators. That
means it will reject some strings that `int(text, 0)` would happily parse. The
payoff is a single, documented grammar and an error type that tells you which
character was wrong.

## Grammar

```
literal     := sign? base_digits suffix?
sign        := '+' | '-'
base_digits := '0x' hex+ | '0X' hex+ | '0b' bin+ | '0B' bin+
             | '0o' oct+ | '0O' oct+
suffix      := 'u' | 'U' | 'l' | 'L' | 'll' | 'LL'
```

Suffixes are accepted in any combination of unsigned and long markers, in
either order, case-insensitively. They are validated and then discarded; the
returned value is the magnitude with the sign applied.

## API

### `parse_int(text: str) -> int`

Return the integer value of `text`. Raises `InvalidLiteralError` if `text` is
not a valid literal, and `TypeError` if `text` is not a `str`.

### `InvalidLiteralError`

A subclass of `ValueError`. Catching `ValueError` still works; catching the
narrower type lets you distinguish parser failures from unrelated errors.

## Awkward edge

There is no decimal fallback. `parse_int("123")` raises
`InvalidLiteralError`, because `123` has no radix marker. If you need to accept
plain decimal literals as well, check for a leading `0x`/`0b`/`0o` yourself and
fall back to `int(text, 10)`.

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

