
class CancelIf(Exception): pass

class If:
    def __init__(self, cond):
        self.cond = bool(cond)

    def __enter__(self):
        return self

    def __exit__(self, ex_type, *args):
        if ex_type is CancelIf: return True

    def control(self):
        if not self.cond: raise CancelIf()

def main():
    with If(True) as cond:
        cond.control()
        # print('True')

    with If(False) as cond:
        cond.control()
        # print('False')


def main2():
    if True: pass
        # print('True')

    if False: pass
        # print('False')

        
if __name__ == '__main__':
    for i in range(int(1E6)): main()
