import dis
import types


def count_operations(source_code: types.CodeType) -> dict[str, int]:
    """Count byte code operations in given source code.

    :param source_code: the bytecode operation names to be extracted from
    :return: operation counts
    """
    ans = {}
    for inst in dis.get_instructions(source_code):
        if inst.opname in ans:
            ans[inst.opname] += 1
        else:
            ans[inst.opname] = 1

        if (isinstance((inst.argval), types.CodeType)):
            ans2 = count_operations(inst.argval)

            for k, v in ans2.items():
                if k not in ans:
                    ans[k] = v
                else:
                    ans[k] += v

    return ans

source_code="""
def f():
    a = 1
print(f())
"""

code_object = compile(source_code, '<string>', 'exec')
d = count_operations(code_object)
print(d)

print(dis.dis(code_object))
