"""Parse C-style integer literals with radix markers and suffixes.

The parser is deliberately narrow: it accepts the forms that appear in
C, C++, Java, and Python source for non-decimal integers, and it rejects
everything else.  A single explicit grammar is easier to reason about
than a pile of special cases, and it means callers get a predictable
error instead of a silently wrong value.

Accepted grammar::

    literal := sign? base_digits suffix?
    sign    := '+' | '-'
    base_digits := '0x' hex+ | '0X' hex+ | '0b' bin+ | '0B' bin+
                 | '0o' oct+ | '0O' oct+
    suffix  := 'u' | 'U' | 'l' | 'L' | 'll' | 'LL'

Suffixes are accepted in any combination of unsigned and long markers,
case-insensitively, because real C code mixes them freely.  The value is
returned as a Python ``int``; the suffix is validated and discarded.

Why not use :func:`int` with a base?  Because ``int('0x10', 0)`` accepts
underscores and whitespace, and ``int('0b2', 0)`` raises a generic
``ValueError`` with no position information.  This module gives a
single, well-defined error type and a clear contract.
"""

from __future__ import annotations

from typing import Final

__all__ = ["parse_int", "InvalidLiteralError"]


class InvalidLiteralError(ValueError):
    """Raised when a string is not a valid non-decimal integer literal.

    Subclassing :class:`ValueError` means callers that already catch
    ``ValueError`` keep working, while callers that want to distinguish
    this parser's failures can catch the narrower type.
    """


#: Radix markers, mapped to the base they introduce.  The marker is
#: matched case-insensitively, so both ``0x`` and ``0X`` appear here.
_MARKERS: Final[dict[str, int]] = {
    "0x": 16,
    "0b": 2,
    "0o": 8,
}

#: Characters permitted in each base, as a lookup set.  Using a set
#: avoids a chain of comparisons and makes the allowed alphabet explicit.
_DIGITS: Final[dict[int, frozenset[str]]] = {
    2: frozenset("01"),
    8: frozenset("01234567"),
    16: frozenset("0123456789abcdef"),
}


def _strip_suffix(body: str) -> str:
    """Return *body* with a valid C integer suffix removed.

    The suffix grammar is small enough to handle with a loop rather than
a regex, which keeps the error messages precise.  A suffix is one or
    more of ``u``/``U`` and one or two of ``l``/``L``, in either order.
    """
    # Walk from the end, consuming suffix characters.  We only accept a
    # suffix that is a valid combination; anything else is left in place
    # so the digit check below reports a useful position.
    end = len(body)
    saw_unsigned = False
    saw_long = 0
    while end > 0:
        ch = body[end - 1]
        low = ch.lower()
        if low == "u" and not saw_unsigned:
            saw_unsigned = True
            end -= 1
        elif low == "l" and saw_long < 2:
            saw_long += 1
            end -= 1
        else:
            break
    # A lone ``u`` or ``l`` at the start of the number is not a suffix;
    # the loop would have consumed it, so guard against an empty body.
    if end == 0:
        raise InvalidLiteralError("literal contains no digits")
    return body[:end]


def parse_int(text: str) -> int:
    """Parse a C-style non-decimal integer literal into a Python ``int``.

    Parameters
    ----------
    text:
        The literal to parse.  Leading and trailing whitespace is *not*
        stripped; a literal with surrounding spaces is rejected so that
        callers do not accidentally accept malformed input.

    Returns
    -------
    int
        The value of the literal.  The sign is applied to the magnitude.

    Raises
    ------
    InvalidLiteralError
        If *text* is not a valid non-decimal literal.  The message names
        the offending position where practical.

    Examples
    --------
    >>> parse_int("0xFF")
    255
    >>> parse_int("-0b1010")
    -10
    >>> parse_int("0o17u")
    15
    """
    if not isinstance(text, str):
        raise TypeError(f"expected str, got {type(text).__name__}")
    if not text:
        raise InvalidLiteralError("empty literal")

    original = text
    sign = 1
    if text[0] in "+-":
        if text[0] == "-":
            sign = -1
        text = text[1:]
        if not text:
            raise InvalidLiteralError("sign without digits")

    # The radix marker is the first two characters and must be present;
    # decimal literals are out of scope for this parser.
    marker = text[:2].lower()
    if marker not in _MARKERS:
        raise InvalidLiteralError(
            f"missing radix marker in {original!r}; expected 0x, 0b, or 0o"
        )
    base = _MARKERS[marker]
    digits = text[2:]
    if not digits:
        raise InvalidLiteralError(f"no digits after radix marker in {original!r}")

    digits = _strip_suffix(digits)
    allowed = _DIGITS[base]
    for index, ch in enumerate(digits):
        if ch.lower() not in allowed:
            # Report the position within the whole literal, not just the
            # digit run, so the caller can point at the character.
            offset = len(original) - len(digits) + index
            raise InvalidLiteralError(
                f"invalid digit {ch!r} at position {offset} in {original!r}"
            )

    return sign * int(digits, base)
