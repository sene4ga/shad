"""
Simplified VM code which works for some cases.
You need extend/rewrite code to pass all cases.
"""

import builtins
import dis
import types
import typing as tp

from typing import Any
CO_VARARGS = 4
CO_VARKEYWORDS = 8

ERR_TOO_MANY_POS_ARGS = 'Too many positional arguments'
ERR_TOO_MANY_KW_ARGS = 'Too many keyword arguments'
ERR_MULT_VALUES_FOR_ARG = 'Multiple values for arguments'
ERR_MISSING_POS_ARGS = 'Missing positional arguments'
ERR_MISSING_KWONLY_ARGS = 'Missing keyword-only arguments'
ERR_POSONLY_PASSED_AS_KW = 'Positional-only argument passed as keyword argument'



class NullType:
    def __repr__(self):
        return "NULL"

NULL = NullType()

class Cell:
    def __init__(self, value):
        self.value = value

class VMFunction:
    def __init__(self, vm_frame, code, globals_, builtins_, defaults=(),
                 kwdefaults=None, closure=None, annotations=None):
        self._vm_frame = vm_frame
        self.__code__ = code
        self.__globals__ = globals_
        self.__builtins__ = builtins_
        self.__defaults__ = defaults or ()
        self.__kwdefaults__ = kwdefaults or {}
        self.__closure__ = closure
        self.__annotations__ = annotations or {}
        self.closure = closure

    def __call__(self, *args, **kwargs):
        code = self.__code__

        parsed_args = bind_args(
            code,
            self.__defaults__,
            self.__kwdefaults__,
            *args,
            **kwargs
        )

        if self.__closure__:
            for i, freevar in enumerate(code.co_freevars):
                parsed_args[freevar] = self.__closure__[i]

        frame = Frame(
            code,
            self.__builtins__,
            self.__globals__,
            parsed_args
        )
        return frame.run()


def bind_args(code: types.CodeType,
                      defaults: tuple | None,
                      kwdefaults: dict[str, Any] | None,
                      *args: Any,
                      **kwargs: Any) -> dict[str, Any]:
            co_argcount = code.co_argcount
            co_kwonlyargcount = code.co_kwonlyargcount
            co_varnames = code.co_varnames
            co_posonly = co_varnames[:code.co_posonlyargcount]
            names = co_varnames[:co_argcount]

            if defaults is None:
                defaults = ()

            off = co_argcount - len(defaults)
            ans = {}
            myargs = []
            pos_provided = set()

            for i, arg_name in enumerate(names):
                if i >= off:
                    ans[arg_name] = defaults[i - off]

            for i, arg_val in enumerate(args):
                if i < co_argcount:
                    ans[names[i]] = arg_val
                    pos_provided.add(names[i])
                else:
                    myargs.append(arg_val)

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

            if myargs and not (code.co_flags & CO_VARARGS):
                raise TypeError(ERR_TOO_MANY_POS_ARGS)

            for i in range(off):
                name = names[i]
                if name not in ans:
                    raise TypeError(ERR_MISSING_POS_ARGS)

            if code.co_flags & CO_VARKEYWORDS:
                varkw_name = co_varnames[-1]
                ans[varkw_name] = mykwargs

            if kwdefaults is None:
                kwdefaults = {}
            for name in kwnames:
                if name not in ans:
                    if name in kwdefaults:
                        ans[name] = kwdefaults[name]
                    else:
                        raise TypeError(ERR_MISSING_KWONLY_ARGS)
            return ans

class Frame:
    """
    Frame header in cpython with description
        https://github.com/python/cpython/blob/3.13/Include/internal/pycore_frame.h

    Text description of frame parameters
        https://docs.python.org/3/library/inspect.html?highlight=frame#types-and-members
    """
    def __init__(self,
                 frame_code: types.CodeType,
                 frame_builtins: dict[str, tp.Any],
                 frame_globals: dict[str, tp.Any],
                 frame_locals: dict[str, tp.Any]) -> None:
        self.code = frame_code
        self.builtins = frame_builtins
        self.globals = frame_globals
        self.locals = frame_locals
        self.data_stack: tp.Any = []
        self.return_value = None
        self.last_exception = None
        self.extended_arg = 0

    def top(self) -> tp.Any:
        return self.data_stack[-1]

    def pop(self) -> tp.Any:
        return self.data_stack.pop()

    def push(self, *values: tp.Any) -> None:
        self.data_stack.extend(values)

    def popn(self, n: int) -> tp.Any:
        """
        Pop a number of values from the value stack.
        A list of n values is returned, the deepest value first.
        """
        if n > 0:
            returned = self.data_stack[-n:]
            self.data_stack[-n:] = []
            return returned
        else:
            return []

    def run(self) -> tp.Any:
        instructions = list(dis.get_instructions(self.code))
        self.instructions = instructions
        self.offset_to_index = {instr.offset: i for i, instr in enumerate(instructions)}
        self.instruction_idx = 0
        bytecode = dis.Bytecode(self.code)
        self.exception_entries = list(getattr(bytecode, "exception_entries", []))

        while self.instruction_idx < len(instructions):
            instruction = instructions[self.instruction_idx]
            current_idx = self.instruction_idx

            op = instruction.opname.lower() + "_op"

            if instruction.opname == "LOAD_GLOBAL":
                getattr(self, op)(instruction.arg, instruction.argval)
            elif instruction.arg is None:
                getattr(self, op)(None)
            else:
                getattr(self, op)(instruction.argval)

            if instruction.opname in ("RETURN_VALUE", "RETURN_CONST"):
                return self.return_value

            if self.instruction_idx == current_idx:
                self.instruction_idx += 1
        return self.return_value

    def resume_op(self, arg: int) -> tp.Any:
        pass

    def push_null_op(self, arg=None) -> None:
        self.push(NULL)

    def precall_op(self, arg: int) -> tp.Any:
        pass

    def kw_names_op(self, argval: tuple) -> None:
        self.kw_names = argval

    def call_op(self, argc: int) -> None:
        kw_names = getattr(self, "kw_names", None)

        if kw_names is not None:
            n_kw = len(kw_names)
            named_vals = [self.pop() for _ in range(n_kw)]
            named_vals.reverse()
            kwargs = dict(zip(kw_names, named_vals))

            pos_count = argc - n_kw
            pos_args = [self.pop() for _ in range(pos_count)]
            pos_args.reverse()

            self.kw_names = ()
        else:
            kwargs = {}
            pos_args = self.popn(argc)

        if len(self.data_stack) >= 2 and self.data_stack[-2] is NULL:
            func = self.data_stack[-1]
            self.data_stack.pop()
            self.data_stack.pop()

        elif self.data_stack and self.data_stack[-1] is NULL:
            self.data_stack.pop()
            func = self.pop()

        else:
            func = self.pop()

        result = func(*pos_args, **kwargs)
        self.push(result)

    def call_function_ex_op(self, flags: int) -> None:
        kwargs = {}
        if flags & 0x01:
            kwargs = self.pop()
        args = self.pop()

        if len(self.data_stack) >= 2 and self.data_stack[-2] is NULL:
            func = self.data_stack[-1]
            self.data_stack.pop()
            self.data_stack.pop()
        elif self.data_stack and self.data_stack[-1] is NULL:
            self.data_stack.pop()
            func = self.pop()
        else:
            func = self.pop()

        result = func(*args, **kwargs)
        self.push(result)

    def copy_free_vars_op(self, arg: int) -> None:
        pass

    def load_closure_op(self, name: str) -> None:
        self.push(self.locals[name])

    def load_deref_op(self, name: str) -> None:
        cell = self.locals[name]
        self.push(cell.value)

    def store_deref_op(self, name: str) -> None:
        val = self.pop()
        if name in self.locals and isinstance(self.locals[name], Cell):
            self.locals[name].value = val
        else:
            self.locals[name] = Cell(val)

    def delete_deref_op(self, name: str) -> None:
        if name in self.locals and isinstance(self.locals[name], Cell):
            self.locals[name].value = None
        else:
            raise NameError(f"name '{name}' is not defined")

    def load_name_op(self, arg: str) -> None:
        if arg in self.globals:
            self.push(self.globals[arg])
        elif arg in self.builtins:
            self.push(self.builtins[arg])
        else:
            raise NameError("variable not found")

    def load_global_op(self, raw_arg: int, name: str) -> None:
        push_null = raw_arg & 1

        if name in self.globals:
            value = self.globals[name]
        elif name in self.builtins:
            value = self.builtins[name]
        else:
            from typing import cast
            self.last_exception = cast(None, NameError("name is not defined"))
            self.jump_to_exception_handler()
            return

        if push_null:
            self.push(NULL)

        self.push(value)

    def store_global_op(self, arg: str) -> None:
        const = self.pop()
        self.globals[arg] = const

    def load_const_op(self, arg: tp.Any) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.13.7/library/dis.html#opcode-LOAD_CONST
        """
        self.push(arg)

    def return_value_op(self, arg: tp.Any) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.13.7/library/dis.html#opcode-RETURN_VALUE
        """
        self.return_value = self.pop()

    def return_const_op(self, const: Any) -> None:
        self.push(const)
        self.should_exit = True

    def pop_top_op(self, arg: tp.Any) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.13.7/library/dis.html#opcode-POP_TOP
        """
        if self.data_stack:
            self.pop()

    def make_function_op(self, arg: int) -> None:
        code = self.pop()

        def f(*args, **kwargs):
            current_defaults = getattr(f, '__defaults__', ())
            current_kwdefaults = getattr(f, '__kwdefaults__', {})

            parsed_args = bind_args(code, current_defaults, current_kwdefaults, *args, **kwargs)

            current_closure = getattr(f, '__closure__', None)
            if current_closure:
                for i, freevar in enumerate(code.co_freevars):
                    parsed_args[freevar] = current_closure[i]

            frame = Frame(code, self.builtins, self.globals, parsed_args)
            result = frame.run()

            return frame.locals if code.co_name == "<module>" or code.co_flags & 0x20 else result

        self.push(f)

    def handle_exception(self):
        while self.instruction_idx < len(self.instructions):
            instr = self.instructions[self.instruction_idx]

            if instr.opname == "PUSH_EXC_INFO":
                self.push(self.last_exception)
                return

            self.instruction_idx += 1
        raise self.last_exception

    def load_assertion_error_op(self, arg):
        self.push(AssertionError)

    def load_from_dict_or_globals_op(self, name: str) -> None:
        mapping = self.pop()
        if name in mapping:
            self.push(mapping[name])
        elif name in self.globals:
            self.push(self.globals[name])
        elif name in self.builtins:
            self.push(self.builtins[name])
        else:
            raise NameError(f"name '{name}' is not defined")

    def load_from_dict_or_deref_op(self, name: str) -> None:
        mapping = self.pop()
        if name in mapping:
            self.push(mapping[name])
        else:
            cell = self.locals[name]
            self.push(cell.value)

    def dict_update_op(self, i: int) -> None:
        update_dict = self.pop()
        self.data_stack[-i].update(update_dict)

    def dict_merge_op(self, i: int) -> None:
        update_dict = self.pop()
        self.data_stack[-i].update(update_dict)

    def jump_to_exception_handler(self):
        current_offset = self.instructions[self.instruction_idx].offset

        for entry in self.exception_entries:
            if entry.start <= current_offset < entry.end:
                self.instruction_idx = self.offset_to_index[entry.target]
                return

        raise self.last_exception

    def push_exc_info_op(self, arg):
        self.push(self.last_exception)

    def check_exc_match_op(self, arg):
        exc_type = self.pop()
        exc = self.top()

        self.push(isinstance(exc, exc_type))

    def pop_except_op(self, arg):
        pass

    def delete_name_op(self, name: str) -> None:
        if name in self.locals:
            del self.locals[name]
        elif name in self.globals:
            del self.globals[name]
        else:
            raise NameError(f"name '{name}' is not defined")

    def raise_varargs_op(self, argc: int) -> None:
        if argc == 0:
            if self.last_exception is None:
                raise RuntimeError("No active exception")
            raise self.last_exception

        elif argc == 1:
            exc = self.pop()
            self.last_exception = exc
            self.jump_to_exception_handler()

        elif argc == 2:
            cause = self.pop()
            exc = self.pop()
            raise exc from cause

        else:
            raise ValueError(f"Invalid RAISE_VARARGS argc={argc}")

    def reraise_op(self, argc: int) -> None:
        if self.last_exception is None:
            raise RuntimeError("No active exception")

        raise self.last_exception

    def before_with_op(self, arg):
        manager = self.pop()

        exit_func = getattr(manager, "__exit__")
        enter_func = getattr(manager, "__enter__")

        result = enter_func()

        self.push(exit_func)
        self.push(result)

    def store_name_op(self, arg: str) -> None:
        """
        Operation description:
            https://docs.python.org/release/3.13.7/library/dis.html#opcode-STORE_NAME
        """
        const = self.pop()
        self.locals[arg] = const

    def get_iter_op(self, arg) -> None:
        obj = self.pop()
        self.push(iter(obj))

    def for_iter_op(self, target_offset: int) -> None:
        it = self.data_stack[-1]
        try:
            value = next(it)
            self.push(value)
        except StopIteration:
            self.instruction_idx = self.offset_to_index[target_offset]

    def end_for_op(self, arg) -> None:
        if len(self.data_stack) >= 2:
            self.pop()
            next_instr = self.instructions[self.instruction_idx]
            if next_instr.opname == "POP_TOP":
                self.instruction_idx += 1
        else:
            self.pop()

    def jump_backward_op(self, target_offset: int) -> None:
        self.instruction_idx = self.offset_to_index[target_offset]

    def jump_forward_op(self, target_offset: int) -> None:
        self.instruction_idx = self.offset_to_index[target_offset]

    def unpack_sequence_op(self, count: int) -> None:
        top = self.pop()
        if not hasattr(top, "__len__") or len(top) != count:
            raise ValueError(f"UNPACK_SEQUENCE expected {count} elements, got {top!r}")
        self.data_stack.extend(reversed(top))

    def pop_jump_if_false_op(self, target_offset: int) -> None:
        value = self.pop()
        if not value:
            self.instruction_idx = self.offset_to_index[target_offset]

    def pop_jump_if_true_op(self, target_offset: int) -> None:
        value = self.pop()
        if value:
            self.instruction_idx = self.offset_to_index[target_offset]

    def pop_jump_if_none_op(self, target_offset: int) -> None:
        value = self.pop()
        if value is None:
            self.instruction_idx = self.offset_to_index[target_offset]

    def binary_slice_op(self, delta: int) -> None:
        end = self.pop()
        start = self.pop()
        cont = self.pop()
        self.push(cont[start:end])

    def build_slice_op(self, argc: int) -> None:
        if argc == 2:
            end = self.pop()
            start = self.pop()
            self.push(slice(start, end))
        elif argc == 3:
            step = self.pop()
            end = self.pop()
            start = self.pop()
            self.push(slice(start, end, step))

    def binary_subscr_op(self, argc: int) -> None:
        rhs = self.pop()
        lhs = self.pop()
        self.push(lhs[rhs])

    def build_list_op(self, argc: int) -> None:
        if argc == 0:
            self.push([])
        else:
            items = self.popn(argc)
            self.push(list(items))

    def store_slice_op(self, argc: int) -> None:
        end = self.pop()
        start = self.pop()
        cont = self.pop()
        val = self.pop()
        cont[start:end] = val

    def delete_subscr_op(self, argc: int) -> None:
        key = self.pop()
        cont = self.pop()
        del cont[key]

    def list_extend_op(self, i: int) -> None:
        seq = self.pop()
        list.extend(self.data_stack[-i], seq)

    def build_const_key_map_op(self, count: int) -> None:
        keys = self.pop()
        values = [self.pop() for _ in range(count)]

        values.reverse()
        result = {k: v for k, v in zip(keys, values)}

        self.push(result)

    def build_set_op(self, argc: int) -> None:
        if argc == 0:
            self.push(set())
        else:
            items = self.popn(argc)
            self.push(set(items))

    def set_update_op(self, i: int) -> None:
        seq = self.pop()
        set.update(self.data_stack[-i], seq)

    def convert_value_op(self, i: int) -> None:
        val = self.pop()

        if i == 0:
            self.push(val)
        elif i == 1:
            self.push(str(val))
        elif i == 2:
            self.push(repr(val))
        elif i == 3:
            self.push(ascii(val))

    def format_simple_op(self, i) -> None:
        val = self.pop()
        self.push(str(val))

    def format_value_op(self, flags: int) -> None:
        val = self.pop()
        if (flags & 0x03) == 0:
            val = str(val)
        elif (flags & 0x03) == 1:
            val = repr(val)
        elif (flags & 0x03) == 2:
            val = ascii(val)
        self.push(val)

    def with_except_start_op(self, arg):
        exc = self.top()  # exception instance

        exit_func = self.data_stack[-2]

        result = exit_func(type(exc), exc, None)

        self.push(result)

    def format_with_spec_op(self, arg: int) -> None:
        spec = self.pop()
        val = self.pop()
        self.push(format(val, spec))

    def build_string_op(self, count: int) -> None:
        parts = [self.pop() for _ in range(count)]
        parts.reverse()
        result = ''.join(str(p) for p in parts)
        self.push(result)

    def store_subscr_op(self, i: int) -> None:
        key = self.pop()
        container = self.pop()
        value = self.pop()
        container[key] = value

    def load_fast_op(self, name: str) -> None:
        if name in self.locals:
            self.push(self.locals[name])
        else:
            raise UnboundLocalError(f"local variable '{name}' referenced before assignment")

    def load_fast_and_clear_op(self, name: str) -> None:
        if name in self.locals:
            value = self.locals[name]
            del self.locals[name]
        else:
            value = NULL
        self.push(value)

    def store_fast_load_fast_op(self, name) -> None:
        if isinstance(name, tuple):
            store_name, load_name = name
        else:
            store_name = load_name = name

        value = self.pop()
        self.locals[store_name] = value
        self.push(self.locals[load_name])

    def list_append_op(self, i: int) -> None:
        value = self.pop()
        lst = self.data_stack[-i]
        lst.append(value)

    def swap_op(self, i: int) -> None:
        if i > len(self.data_stack):
            raise RuntimeError(f"SWAP {i} failed, stack={self.data_stack}")
        self.data_stack[-1], self.data_stack[-i] = (
            self.data_stack[-i],
            self.data_stack[-1],
        )

    def unary_negative_op(self, i: int):
        self.data_stack[-1] = -self.data_stack[-1]

    def unary_invert_op(self, i: int):
        self.data_stack[-1] = ~self.data_stack[-1]

    def to_bool_op(self, i: int):
        self.data_stack[-1] = bool(self.data_stack[-1])

    def unary_not_op(self, i: int):
        self.data_stack[-1] = not self.data_stack[-1]

    def call_kw_op(self, argc: int) -> None:
        kw_names = self.pop()
        n_kw = len(kw_names)

        named_vals = [self.pop() for _ in range(n_kw)]
        named_vals.reverse()

        pos_count = argc - n_kw
        pos_args = [self.pop() for _ in range(pos_count)]
        pos_args.reverse()

        kwargs = {kw_names[i]: named_vals[i] for i in range(n_kw)}

        if len(self.data_stack) >= 2 and self.data_stack[-2] is NULL:
            callable_obj = self.data_stack[-1]
            self.data_stack.pop()
            self.data_stack.pop()
        elif self.data_stack and self.data_stack[-1] is NULL:
            self.data_stack.pop()
            callable_obj = self.pop()
        else:
            callable_obj = self.pop()

        result = callable_obj(*pos_args, **kwargs)
        self.push(result)

    def copy_op(self, i: int):
        if i <= len(self.data_stack):
            self.push(self.data_stack[-i])
        else:
            self.push(self.last_exception)

    def load_attr_op(self, name: str) -> None:
        obj = self.pop()
        attr = getattr(obj, name)

        if hasattr(attr, "__self__") and hasattr(attr, "__func__"):
            self.push(NULL)
            self.push(attr.__func__)
            self.push(attr.__self__)
        else:
            self.push(attr)

    def build_map_op(self, count: int):
        pairs = []
        for _ in range(count):
            value = self.pop()
            key = self.pop()
            pairs.append((key, value))
        pairs.reverse()

        result = dict(pairs)
        self.push(result)

    def build_tuple_op(self, count: int):
        if count == 0:
            value = ()
        else:
            value = tuple(self.data_stack[-count:])
            self.data_stack = self.data_stack[:-count]

        self.push(value)

    def nop_op(self, i):
        pass

    def store_fast_op(self, name: str) -> None:
        value = self.pop()
        self.locals[name] = value

    def map_add_op(self, i: int) -> None:
        value = self.pop()
        key = self.pop()
        d = self.data_stack[-i]
        d[key] = value

    def set_function_attribute_op(self, flag: int):
        val = self.pop()
        func = self.pop()

        if not callable(func):
            func, val = val, func

        if flag == 0x01:
            func.__defaults__ = val
        elif flag == 0x02:
            func.__kwdefaults__ = val
        elif flag == 0x04:
            if isinstance(val, tuple):
                it = iter(val)
                val = dict(zip(it, it))
            func.__annotations__ = val
        elif flag == 0x08:
            pass

        self.push(func)

    def load_fast_load_fast_op(self, name: tuple) -> None:
        name1, name2 = name
        self.push(self.locals[name1])
        self.push(self.locals[name2])

    def make_cell_op(self, name: str) -> None:
        val = self.locals.get(name, None)
        self.locals[name] = Cell(val)

    def import_name_op(self, name: str) -> None:
        """Импортирует модуль по имени."""
        fromlist = self.pop()
        level = self.pop()
        module = builtins.__import__(name, self.globals, self.locals, fromlist, level)
        self.push(module)

    def import_from_op(self, name: str) -> None:
        module = self.top()
        try:
            value = getattr(module, name)
        except AttributeError:
            module_name = getattr(module, '__name__', repr(module))
            raise ImportError(f"cannot import name '{name}' from '{module_name}'") from None
        self.push(value)

    def load_build_class_op(self, name: str) -> None:
        self.push(builtins.__build_class__)

    def setup_annotations_op(self, name: str) -> None:
        if '__annotations__' not in self.locals:
            self.locals['__annotations__'] = {}

    def store_attr_op(self, name: str) -> None:
        obj = self.pop()
        value = self.pop()
        setattr(obj, name, value)

    def delete_attr_op(self, name: str) -> None:
        obj = self.pop()
        try:
            delattr(obj, name)
        except Exception:
            self.last_exception: Exception | None = None
            self.jump_to_exception_handler()

    def extended_arg_op(self, arg):
        self.extended_arg = arg

    def unpack_ex_op(self, arg: int):
        seq = self.pop()
        seq = list(seq)
        start = arg & 0xFF
        end = arg >> 8

        left = seq[:start]
        r = seq[len(seq) - end:]
        mid = seq[start:len(seq) - end]

        for val in reversed(r):
            self.push(val)

        self.push(mid)

        for val in reversed(left):
            self.push(val)


    def is_op_op(self, arg):
        right = self.pop()
        left = self.pop()
        result = left is not right if (arg & 1) else left is right
        self.push(result)

    def call_intrinsic_1_op(self, oparg: int) -> None:
        arg = self.pop()
        result = None

        if oparg == 0:
            raise RuntimeError("Invalid intrinsic function")
        elif oparg == 1:
            print(arg)
            result = None
        elif oparg == 2:
            if isinstance(arg, str):
                module = builtins.__import__(arg, self.globals, self.locals, [], 0)
            else:
                module = arg
            if hasattr(module, '__all__'):
                names = module.__all__
            else:
                names = [name for name in dir(module) if not name.startswith('_')]
            for name in names:
                value = getattr(module, name)
                self.locals[name] = value
                self.globals[name] = value
            result = None
        elif oparg == 3:
            if isinstance(arg, StopIteration):
                result = arg.value
            else:
                raise TypeError("Expected StopIteration")
        elif oparg == 4:
            raise NotImplementedError("INTRINSIC_ASYNC_GEN_WRAP not implemented")
        elif oparg == 5:
            result = +arg
        elif oparg == 6:
            if isinstance(arg, list):
                result = tuple(arg)
            else:
                raise TypeError("Expected list")

        self.push(result)

    def contains_op_op(self, arg: int):
        right = self.pop()
        left = self.pop()
        result = left in right
        if arg:
            result = not result
        self.push(result)

    def compare_op_op(self, arg: str) -> None:
        import operator

        cmp_ops = {
            "<": operator.lt,
            "<=": operator.le,
            "==": operator.eq,
            "!=": operator.ne,
            ">": operator.gt,
            ">=": operator.ge,
            "in": lambda a, b: a in b,
            "not in": lambda a, b: a not in b,
            "is": lambda a, b: a is b,
            "is not": lambda a, b: a is not b,
            "exception match": operator.contains
        }

        force_bool = False
        if isinstance(arg, str) and ":bool" in arg:
            force_bool = True
            arg = arg[:-5]

        right = self.pop()
        left = self.pop()

        result = cmp_ops[arg](left, right)

        if force_bool:
            result = bool(result)

        self.push(result)

    def binary_op_op(self, oparg: int):
        import operator
        right = self.pop()
        left = self.pop()

        ops = {
            0: operator.add,  # +
            1: operator.and_,  # &
            2: operator.floordiv,  # //
            3: operator.lshift,  # <<
            4: operator.matmul,  # @
            5: operator.mul,  # *
            6: operator.mod,  # %
            7: operator.or_,  # |
            8: operator.pow,  # **
            9: operator.rshift,  # >>
            10: operator.sub,  # -
            11: operator.truediv,  # /
            12: operator.xor,  # ^

            # inplace operations
            13: operator.iadd,
            14: operator.iand,
            15: operator.ifloordiv,
            16: operator.ilshift,
            17: operator.imatmul,
            18: operator.imul,
            19: operator.imod,
            20: operator.ior,
            21: operator.ipow,
            22: operator.irshift,
            23: operator.isub,
            24: operator.itruediv,
            25: operator.ixor,
            88: operator.eq
        }

        if oparg not in ops:
            raise NotImplementedError(f"BINARY_OP {oparg} not implemented")

        result = ops[oparg](left, right)
        self.push(result)


class VirtualMachine:
    def run(self, code_obj: types.CodeType) -> None:
        """
        :param code_obj: code for interpreting
        """
        globals_context: dict[str, tp.Any] = {}
        frame = Frame(code_obj, builtins.globals()['__builtins__'], globals_context, globals_context)
        return frame.run()
