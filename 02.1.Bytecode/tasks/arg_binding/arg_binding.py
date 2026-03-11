from types import FunctionType
from typing import Any
CO_VARARGS = 4
CO_VARKEYWORDS = 8

ERR_TOO_MANY_POS_ARGS = 'Too many positional arguments'
ERR_TOO_MANY_KW_ARGS = 'Too many keyword arguments'
ERR_MULT_VALUES_FOR_ARG = 'Multiple values for arguments'
ERR_MISSING_POS_ARGS = 'Missing positional arguments'
ERR_MISSING_KWONLY_ARGS = 'Missing keyword-only arguments'
ERR_POSONLY_PASSED_AS_KW = 'Positional-only argument passed as keyword argument'


def bind_args(func: FunctionType, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """Bind values from `args` and `kwargs` to corresponding arguments of `func`

    :param func: function to be inspected
    :param args: positional arguments to be bound
    :param kwargs: keyword arguments to be bound
    :return: `dict[argument_name] = argument_value` if binding was successful,
             raise TypeError with one of `ERR_*` error descriptions otherwise
    """
    code = func.__code__
    co_argcount = code.co_argcount
    co_kwonlyargcount = code.co_kwonlyargcount
    co_varnames = code.co_varnames
    co_posonly = co_varnames[:code.co_posonlyargcount]
    names = co_varnames[:co_argcount]
    defaults = func.__defaults__
    if defaults is None:
        defaults = ()

    off = co_argcount - len(defaults)
    ans = {}
    myargs = []
    pos_provided = set()

    for i, arg in enumerate(names):
        if i >= off:
            ans[arg] = defaults[i - off]

    for i, arg in enumerate(args):
        if i < co_argcount:
            ans[names[i]] = arg
            pos_provided.add(names[i])
        else:
            myargs.append(arg)

    if code.co_flags & CO_VARARGS:
        if code.co_flags & CO_VARARGS:
            varargs_name = co_varnames[co_argcount + co_kwonlyargcount]
            ans[varargs_name] = tuple(myargs)

    mykwargs = {}
    kwnames = co_varnames[co_argcount:co_kwonlyargcount + co_argcount]
    for k, v in kwargs.items():
        if k in co_posonly:
            if code.co_flags & CO_VARKEYWORDS:
                mykwargs[k] = v
                continue
            raise TypeError(ERR_POSONLY_PASSED_AS_KW)

        if k in names:
            if k in pos_provided:
                raise TypeError(ERR_MULT_VALUES_FOR_ARG)


        if k in kwnames or k in names:
            ans[k] = v
        elif code.co_flags & CO_VARKEYWORDS:
            mykwargs[k] = v
        else:
            raise TypeError(ERR_TOO_MANY_KW_ARGS)


    if myargs and not(code.co_flags & CO_VARARGS):
        raise TypeError(ERR_TOO_MANY_POS_ARGS)

    for i in range(off):
        name = names[i]
        if name not in ans:
            raise TypeError(ERR_MISSING_POS_ARGS)

    if code.co_flags & CO_VARKEYWORDS:
        varkw_name = co_varnames[-1]
        ans[varkw_name] = mykwargs

    kwdefaults = func.__kwdefaults__ or {}
    for name in kwnames:
        if name not in ans:
            if name in kwdefaults:
                ans[name] = kwdefaults[name]
            else:
                raise TypeError(ERR_MISSING_KWONLY_ARGS)
    return ans


