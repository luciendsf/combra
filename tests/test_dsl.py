import sys
sys.path.append('../')

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
    def foo():
        locals()['eoeo'] = 12
        print('result', locals())
        a = A()
        b = A()
        a <= b
        if a.driver is not b: raise Exception()

    foo()


if __name__ == '__main__':
    test_override_assigment_op()
