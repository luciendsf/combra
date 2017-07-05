import sys
sys.path.append('../')
sys.path.append('.')

from combra.dsl import mod_ast as hw

def test_basic():

    @hw
    def foo():
        print('inside foo')

    foo()


# @hw
# def foo():
#     a = Data()
#     b = Data()
#     a <= b

def test_override_assigment_op():

    from combra.dsl import WithAssign

    class A(WithAssign):
        def __init__(self):
            self.driver = None

        def assign(self, that):
            self.driver = that

        def __le__(self, that):
            raise Exception()

    @hw
    def foo(initvar=12):
        a = A()
        b = A()
        a <= b
        if a.driver is not b: raise Exception()

    foo()

def test_if_else():

    from combra.dsl import WithAssign

    class A(WithAssign):
        def __init__(self):
            self.driver = None

        def assign(self, that):
            self.driver = that

        def __le__(self, that):
            raise Exception()

    @hw
    def foo():
        a = A()
        b = A()

        ifc = None
        elsec = None
        if a: ifc = True
        else: elsec = True

        if not (ifc and elsec): raise Exception()

        if True: pass
        else: raise Exception()

        e = False
        if e: raise Exception()
        else: pass

        b <= 1 if a else 0
        b.assign(mux(a, 1, 0))

    # foo()

from combra.dsl import WithAssign
class A(WithAssign):
    def __init__(self):
        self.driver = None

    def assign(self, that):
        self.driver = that

    def __le__(self, that):
        raise Exception()

def test_if():
    @hw
    def fo2o():
        a = A()
        b = A()
        if True:
            print('first true')
            if False: print('True!')
        else: print('False!')
    fo2o()

if __name__ == '__main__':
    test_if()
    # test_basic()
    # test_override_assigment_op()
