
from .dsl import WithAssign

class Data(WithAssign):
    def __init__(self): pass

    def assign(self, that): print('{} <= {}'.format(self, that))
