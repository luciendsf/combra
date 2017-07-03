
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
                                               id='__assign__'),
                                 args=[cmp_node.left,
                                       cmp_node.comparators[0]],
                                 starargs=None,
                                 kwargs=None,
                                 keywords=[])

            node.value = ast.copy_location(call_node, cmp_node)
            return node

class WithAssign:
    def assign(self, that): raise NotImplementedError()

def __assign__(a, b):
    if isinstance(a, WithAssign): return a.assign(b)
    else: return a <= b


def assign_stack_mod(glob, loc): pass
    
    
mod_ast_modifiers = [OverrideAssignmentOp()]
mod_stack_modifiers = [assign_stack_mod]
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

    for mod in mod_ast_modifiers: a = mod.visit(a)

    print('ast')
    # print(ast.dump(a))
    print(astpretty.pprint(a))

    # compile and exec code in previous global env
    c = compile(a, src_file, mode='exec')

    caller_globals = inspect.stack()[1][0].f_globals
    caller_locals = inspect.stack()[1][0].f_locals

    print('caller loc', caller_locals)
    for (v, k) in mod_ast_global_modifiers: caller_globals[k] = v

    exec(c, caller_globals, caller_locals)

    modfunc = caller_locals[func.__name__]

    return modfunc
