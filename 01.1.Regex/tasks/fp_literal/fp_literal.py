import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class FPLiteral:
    integral: str
    fractional: str
    exp: Optional[str] = None


RE_FP_LITERAL = (
    r'\s*(?:'
    r'((?P<int1>\d+)\.(?P<frac1>\d*))|'
    r'(\.(?P<frac2>\d+))|'
    r'((?P<int3>\d+)(?=[eE]))'
    r')(?:[eE](?P<exp>[+-]?\d+))?'
    r'(?=\s|$|[*/+-])'
)


def f_repr_fp_literal(m: re.Match[str]) -> FPLiteral:
    if m.group('int1') is not None:
        integral = m.group('int1')
        fractional = m.group('frac1')
    elif m.group('int3') is not None:
        integral = m.group('int3')
        fractional = ''
    else:
        integral = ''
        fractional = m.group('frac2')

    exp = m.group('exp')
    return FPLiteral(integral=integral, fractional=fractional, exp=exp)
