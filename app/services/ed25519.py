"""Minimal, dependency-free Ed25519 (RFC 8032) implementation.

Used for the product-key licensing system: the vendor signs a machine's
fingerprint with the *private* key (kept secret, never shipped) and the
application verifies that signature with the embedded *public* key. Because
the application only ever holds the public key, valid product keys cannot be
forged without the vendor's private key.

This is the well-known public-domain reference implementation; it is only
used a couple of times at start-up so its speed is irrelevant.
"""

from __future__ import annotations

import hashlib

b = 256
q = 2 ** 255 - 19
_l = 2 ** 252 + 27742317777372353535851937790883648493


def _H(m: bytes) -> bytes:
    return hashlib.sha512(m).digest()


def _inv(x: int) -> int:
    return pow(x, q - 2, q)


_d = -121665 * _inv(121666) % q
_I = pow(2, (q - 1) // 4, q)


def _xrecover(y: int) -> int:
    xx = (y * y - 1) * _inv(_d * y * y + 1)
    x = pow(xx, (q + 3) // 8, q)
    if (x * x - xx) % q != 0:
        x = (x * _I) % q
    if x % 2 != 0:
        x = q - x
    return x


_By = 4 * _inv(5)
_Bx = _xrecover(_By)
_B = [_Bx % q, _By % q]


def _edwards(P, Q):
    x1, y1 = P
    x2, y2 = Q
    x3 = (x1 * y2 + x2 * y1) * _inv(1 + _d * x1 * x2 * y1 * y2)
    y3 = (y1 * y2 + x1 * x2) * _inv(1 - _d * x1 * x2 * y1 * y2)
    return [x3 % q, y3 % q]


def _scalarmult(P, e):
    """Iterative double-and-add to avoid deep recursion."""
    result = [0, 1]
    addend = P
    while e > 0:
        if e & 1:
            result = _edwards(result, addend)
        addend = _edwards(addend, addend)
        e >>= 1
    return result


def _bit(h: bytes, i: int) -> int:
    return (h[i // 8] >> (i % 8)) & 1


def _encodeint(y: int) -> bytes:
    bits = [(y >> i) & 1 for i in range(b)]
    return bytes(sum(bits[i * 8 + j] << j for j in range(8)) for i in range(b // 8))


def _encodepoint(P) -> bytes:
    x, y = P
    bits = [(y >> i) & 1 for i in range(b - 1)] + [x & 1]
    return bytes(sum(bits[i * 8 + j] << j for j in range(8)) for i in range(b // 8))


def _Hint(m: bytes) -> int:
    h = _H(m)
    return sum(2 ** i * _bit(h, i) for i in range(2 * b))


def publickey(sk: bytes) -> bytes:
    h = _H(sk)
    a = 2 ** (b - 2) + sum(2 ** i * _bit(h, i) for i in range(3, b - 2))
    A = _scalarmult(_B, a)
    return _encodepoint(A)


def signature(m: bytes, sk: bytes, pk: bytes) -> bytes:
    h = _H(sk)
    a = 2 ** (b - 2) + sum(2 ** i * _bit(h, i) for i in range(3, b - 2))
    r = _Hint(bytes(h[j] for j in range(b // 8, b // 4)) + m)
    R = _scalarmult(_B, r)
    S = (r + _Hint(_encodepoint(R) + pk + m) * a) % _l
    return _encodepoint(R) + _encodeint(S)


def _isoncurve(P) -> bool:
    x, y = P
    return (-x * x + y * y - 1 - _d * x * x * y * y) % q == 0


def _decodeint(s: bytes) -> int:
    return sum(2 ** i * _bit(s, i) for i in range(0, b))


def _decodepoint(s: bytes):
    y = sum(2 ** i * _bit(s, i) for i in range(0, b - 1))
    x = _xrecover(y)
    if x & 1 != _bit(s, b - 1):
        x = q - x
    P = [x, y]
    if not _isoncurve(P):
        raise ValueError("point off curve")
    return P


def checkvalid(sig: bytes, m: bytes, pk: bytes) -> bool:
    """Return True if *sig* is a valid Ed25519 signature of *m* under *pk*."""
    try:
        if len(sig) != b // 4 or len(pk) != b // 8:
            return False
        R = _decodepoint(sig[0:b // 8])
        A = _decodepoint(pk)
        S = _decodeint(sig[b // 8:b // 4])
        h = _Hint(_encodepoint(R) + pk + m)
        return _scalarmult(_B, S) == _edwards(R, _scalarmult(A, h))
    except (ValueError, IndexError):
        return False
