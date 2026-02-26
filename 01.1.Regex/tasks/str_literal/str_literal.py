import re

RE_STR_LITERAL = r'''
^\s*
(
    "
    (?:
        \\[nt\\"]        # \n \t \\ \"
        | [^\\\n\t"]
    )*
    "
  |
    '
    (?:
        \\[nt\\']        # \n \t \\ \'
        | [^\\\n\t']
    )*
    '
)
'''

RE_STR_LITERAL = re.compile(RE_STR_LITERAL, re.VERBOSE)


def f_repr_str_literal(m: re.Match[str]) -> str:
    return m.group(1)
