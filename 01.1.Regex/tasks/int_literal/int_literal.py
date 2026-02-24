import re


RE_INT_LITERAL = r'\s*(?:(?P<int1>\d+)|(?P<int2>0[xX][0-9a-fA-F]+))(?=\s|$|[+\-*/%^&|~=<>!])'

def f_repr_int_literal(m: re.Match[str]) -> str:
    if m.group('int1') is not None:
        return m.group('int1')
    return m.group('int2')

