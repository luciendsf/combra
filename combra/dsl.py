
from functools import reduce

import re
import inspect
import ast

import astpretty

class OverrideAssignmentOp(ast.NodeTransformer):
    def visit_Expr(self, node):
            if not isinstance(node.value, ast.Compare): return node
            cmp_node = node.value
            op_name = '__%s__'%(cmp_node.ops[0].__class__.__name__)
            if op_name != '__LtE__': return node
            call_node = ast.Call(lineno=cmp_node.lineno,
                                 col_offset=0,
                                 func=ast.Name(lineno=cmp_node.lineno,
                                               col_offset=0,
                                               ctx=ast.Load(),
                                               id='__combra_assign__'),
                                 args=[cmp_node.left,
                                       cmp_node.comparators[0]],
                                 starargs=None,
                                 kwargs=None,
                                 keywords=[])

            node.value = ast.copy_location(call_node, cmp_node)
            return node

class WithAssign:
    def assign(self, that): return NotImplemented

def __combra_assign__(a, b):
    if isinstance(a, WithAssign): return a.assign(b)
    return a <= b

class OverrideIfElse(ast.NodeTransformer):
    def visit_If(self, node):
        lineno = node.lineno
        col_offset = node.col_offset
        if_test = node.test
        if_body = node.body
        else_body = node.orelse

        test_call = ast.Call(lineno=lineno, col_offset=col_offset,
                             func=ast.Name(
                                 lineno=lineno,
                                 col_offset=col_offset,
                                 id='__combra_if_else__' if else_body else '__combra_if__',
                                 ctx=ast.Load()),
                             args=[if_test],
                             keywords=[])

        control_call = ast.Expr(lineno=lineno, col_offset=col_offset,
                                value=ast.Call(lineno=lineno, col_offset=col_offset,
                                               func=ast.Name(lineno=lineno,
                                                             col_offset=col_offset,
                                                             id='__combra_control__',
                                                             ctx=ast.Load()),
                                               args=[],
                                               keywords=[]))

        if_body.insert(0, control_call)

        withnode = ast.With(lineno=lineno, col_offset=col_offset,
                            items = [ast.withitem(
                                context_expr=test_call,
                                optional_vars=None)],
                            body=if_body)

        self.visit(withnode)

        if not else_body: return withnode

        # else body -> new with node
        test_call_else = ast.Call(lineno=lineno, col_offset=col_offset,
                                  func=ast.Name(lineno=lineno,
                                                col_offset=col_offset,
                                                id='__combra_else__',
                                                ctx=ast.Load()),
                                  args=[],
                                  keywords=[])

        else_control_call = ast.Expr(lineno=lineno, col_offset=col_offset,
                                     value=ast.Call(lineno=lineno, col_offset=col_offset,
                                                    func=ast.Name(
                                                        lineno=lineno,
                                                        col_offset=col_offset,
                                                        id='__combra_control__',
                                                        ctx=ast.Load()),
                                                    args=[],
                                                    keywords=[]))

        else_body.insert(0, else_control_call)

        withnode_else = ast.With(lineno=lineno, col_offset=col_offset,
                                 items = [ast.withitem(
                                     context_expr=test_call_else,
                                     optional_vars=None)],
                                 body=else_body)

        self.visit(withnode_else)

        return [withnode, withnode_else]

class BlockContext:
    stack = []

class ConditionalBlock:
    def if_context(self): return NotImplemented
    def if_with_else_context(self): return NotImplemented
    def else_context(self): return NotImplemented

class CustomConditionalBlock(ConditionalBlock): pass

class StaticBlockAbort(Exception): pass

class StaticBlockContext(BlockContext): pass

class StaticContextIf(StaticBlockContext):
    def __init__(self, cond):
        self.cond = bool(cond)
        BlockContext.stack.append(self)
    def __enter__(self): pass
    def __exit__(self, ex_type, *args):
        BlockContext.stack.pop()
        if ex_type is StaticBlockAbort: return True

class StaticContextIfElse(StaticBlockContext):
    def __init__(self, cond):
        self.cond = BlockContext.stack[-1].cond
        BlockContext.stack.append(self)
    def __enter__(self): pass
    def __exit__(self, ex_type, *args):
        BlockContext.stack.pop()
        StaticContextIfElse_last_cond = self.cond
        if ex_type is StaticBlockAbort: return True

class StaticContextElse(StaticBlockContext):
    def __init__(self):
        self.cond = not StaticContextIfElse_last_cond
        BlockContext.stack.append(self)
    def __enter__(self): pass
    def __exit__(self, ex_type, *args):
        BlockContext.stack.pop()
        if ex_type is StaticBlockAbort: return True


def __combra_if__(test):
    if isinstance(test, CustomConditionalBlock): return test.if_context()
    return StaticContextIf(test)

def __combra_if_else__(test):
    if isinstance(test, CustomConditionalBlock): return test.if_with_else_context(test)
    return StaticContextIfElse(test)

def __combra_else__():
    last_if_else = 
    if isinstance(last_if_else, CustomConditionalBlock): return last_if_else.else_context()
    return StaticContextElse()

def __combra_control__():
    last_block = BlockContext.stack[-1]
    if isinstance(last_block, StaticBlockContext) and not last_block.cond:
        raise StaticBlockAbort()

mod_ast_modifiers = [OverrideAssignmentOp(), OverrideIfElse()]
mod_ast_global_modifiers = [(__combra_assign__, '__combra_assign__'),
                            (__combra_if__, '__combra_if__'),
                            (__combra_if_else__, '__combra_if_else__'),
                            (__combra_control__, '__combra_control__'),
                            (__combra_else__, '__combra_else__')]

mod_ast_re_indent = re.compile(r'( *).+')
def mod_ast(func):
    src, line_num = inspect.getsourcelines(func)
    src_file = inspect.getabsfile(func)
    # print(src_file)

    # remove global indent
    indent = len(mod_ast_re_indent.match(src[0]).group(1))
    src = [l[indent:] for l in src]
    src = reduce(lambda x, y: x+y, src)

    # print('\nsources of {}'.format(func.__name__))
    # for l in src: print(l, end='')

    # pad with empty lines to match line numbering
    src = '\n'*(line_num-1) + src

    # get ast
    a = ast.parse(src)

    # remove the first decorator applied, presumably this one
    a.body[0].decorator_list = a.body[0].decorator_list[:-1]

    # # inherit caller locals callback
    # mod_ast_inherit_locals(a.body[0])

    print('='*10+'ast before')
    print(astpretty.pprint(a))

    for mod in mod_ast_modifiers: a = mod.visit(a)

    print('='*10+'ast after')
    print(astpretty.pprint(a))

    # compile and exec code in previous global env
    c = compile(a, src_file, mode='exec')

    caller_globals = inspect.stack()[1][0].f_globals
    caller_locals = inspect.stack()[1][0].f_locals

    global mod_ast_last_caller_locals
    mod_ast_last_caller_locals = caller_locals

    for (v, k) in mod_ast_global_modifiers: caller_globals[k] = v

    # pour locals in global
    # allow sub-funcs to refer to funcs / class declared in the parent func
    caller_globals = dict(caller_globals, **caller_locals)

    # print('in mod, locals', caller_locals)
    # print('in mod, global', caller_globals)

    exec(c, caller_globals, caller_locals)

    modfunc = caller_locals[func.__name__]

    return modfunc
