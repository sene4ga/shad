import re


@dataclass
class FPLiteral():
    integral: str
    fractional: str
    exp: str


RE_FP_LITERAL = ...


def f_repr_fp_literal(m: re.Match[str]) -> FPLiteral:
    ...

