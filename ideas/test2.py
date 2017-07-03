
class Data:
    def __le__(self, that):
        print('{} <= {}'.format(self, that))
        self.next = that
        try: that.readers.append(self)
        except: pass

class Bool(Data): pass

class Bundle(Data): pass


import inspect
import ast
import re

from functools import reduce

import astpretty

from caerbanlog.sync import reg
from caerbanlog.async import latch
from caerbanlog.bus.amba.axi4 import axi4lite


hw_re_indent = r'( *).+'
hw_re_indent_c = re.compile(hw_re_indent)
def hw(func):
    src, line_num = inspect.getsourcelines(func)
    src_file = inspect.getabsfile(func)
    # print(src_file)

    # remove global indent
    indent = len(hw_re_indent_c.match(src[0]).group(1))
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

    # tweaking the ast :D
    class RewriteExprCompare(ast.NodeTransformer):
        def visit_Expr(self, node):
            if not isinstance(node.value, ast.Compare): return node
            cmp_node = node.value
            id = '__%s__'%(cmp_node.ops[0].__class__.__name__)
            call_node = ast.Call(func=ast.copy_location(ast.Name(lineno=cmp_node.lineno,
                                                                 col_offset=0,
                                                                 ctx=ast.Load(),
                                                                 id=id),
                                                        cmp_node),
                                 args=[cmp_node.left,
                                       cmp_node.comparators[0]],
                                 keywords=[])

            node.value = ast.copy_location(call_node, cmp_node)
            return node

    class RewriteIfExpCompare(ast.NodeTransformer):
        def visit_IfExp(self, node):
            if not isinstance(node.body, ast.Compare): return node
            return node

    a = RewriteExprCompare().visit(a)
    a = RewriteIfExpCompare().visit(a)

    print('ast')
    print(astpretty.pprint(a))

    # compile and exec code in previous global env
    c = compile(a, src_file, mode='exec')
    # caller_globals = inspect.stack(context=0)[0].frame.f_globals
    caller_globals = inspect.stack(context=0)[0][0].f_globals
    locals_result = {}
    exec(c, caller_globals, locals_result)

    modfunc = locals_result[func.__name__]

    def f(*args, **kwargs): modfunc(*args, **kwargs)

    return f

def __LtE__(this, that):
    print('{} <= {}'.format(this, that))

def placed(func): return func

class Interface(Bundle):
    def __init__(self):
        self.sclk = Bool()
        self.sdi = Bool()
        self.sdo = Bool()
        self.sync = Bool()

    @hw
    def as_master(self):
        output(self.sclk, self.sdi, self.sync)
        input(self.sdo)

    @hw
    def ioBuffer(self, latch_cond):
        buffered = Interface()
        buffered.sclk <= regNext(self.sclk)
        return buffered

    @placed
    @hw
    def send(self, value):
        def reg(c): return c
        def uint(cc): return cc
        class Bits:
            def __mul__(self, that):
                print('mul works ???')
                return self

        bits = Bits()
        wow = Reg(Int(signed_bits=16))
        kah = regnext(wow).init(0)
        ber = Reg(Int(bits=16))
        print('heello')
        wow <= 42
        if wow <= 2E6: print('if block')
        else: print('else block')
        a, b, c, d, e, f = 12

i = Interface()
i.send(42)

def mul(gain, input):
    op = Op()
    op.in_p - gnd
    op.in_n - ((r10k / c10n) - op.out) - (r10k - input)
    return op.out

def soc():
    stcmp = StCmp()
    sdram = Sdram()
    stcmp.sdram - sdram - pullup(r10k, sdram.power.vdd)
