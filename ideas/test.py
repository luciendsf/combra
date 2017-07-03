
a = 12

from typing import TypeVar, Generic
from typing import overload

class Data:
    def assign(self, that): pass

    def __le__(self, that):
        self.assign(that)

    def __and__(self, that):
        return self

    def clone(self):
        return self

class Bool(Data):
    def __invert__(self):
        return Data()

class BitVector(Data):
    def __init__(self, width=None):
        Data.__init__(self)
        self.width = width

class Int(BitVector):
    def __init__(self, width=None):
        BitVector.__init__(self, width=width)

class UInt(Int):
    def __init__(self, width=None):
        Int.__init__(self, width=width)

class Area: pass

class Bundle(Data, Area):
    def to_verilog(self):
        for d in filter(lambda x: isinstance(x, Data) , self.__dict__.values()):
            d.to_verilog()

def push_condition(cond): pass
def pop_condition(cond = None): pass

T = TypeVar('T', bound=Data)
class Stream(Bundle, Generic[T]):
    def __init__(self, data : T):
        Bundle.__init__(self)
        self.payload = data
        self.valid = Bool()
        self.ready = Bool()

    def weak_pull(self):
        self.ready <= ~self.valid

    def will_fire(self):
        return self.valid & self.ready

    class Puller(object):
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            self.stream.ready <= True
            push_condition(self.stream.will_fire())
            return self.stream.payload

        def __exit__(self, *args):
            pop_condition()

    def pull(self): return Stream.Puller(self)

    class Pusher(object):
        def __init__(self, stream, value):
            self.stream = stream
            self.value = value

        def __enter__(self):
            self.stream.valid <= True
            push_condition(self.stream.will_fire())
            return self.stream.payload

        def __exit__(self, *args):
            pop_condition()

    def push(self, value): return Stream.Pusher(self, value)

def slave(a_type): return a_type
def master(a_type): return a_type

class Float(Bundle):
    def __init__(self, width=None, mantissa_width=None, exponent_width = None):
        Bundle.__init__(self)
        self.mantissa = UInt(width=mantissa_width)
        self.exponent = UInt(width=exponent_width)


class State(Area):
    def __init__(self, name, parent_fsm):
        self.parent = parent_fsm

    def __enter__(self): return self
    def __exit__(self, *args): pass

class Fsm(Area):
    def __getattr__(self, name):
        new_state = State(name, self)
        self.__setattr__(name, new_state)
        return new_state

def goto(state): return 0

def reg(data : Data) -> Data:
    return data

def clone(data : Data) -> Data:
    return data.clone()

class KeyPoints(Bundle):
    def __init__(self):
        Bundle.__init__(self)
        self.end_value = UInt(width=10)
        self.delay = Float(width=10, mantissa_width=4)


def interpolate(keyPoints : slave(Stream[KeyPoints])) -> master(Stream[Data]):

    keyPoints.weak_pull()

    interpolated_values = master(Stream(UInt(width=16)))

    fsm = Fsm()

    last_keypoint = reg(clone(keyPoints.payload))
    with fsm.state1:
        with keyPoints.pull() as keyPoint:
            last_keypoint <= keyPoint
            goto(fsm.state2)

    with fsm.state2:
        with interpolated_values.push(last_keypoint.end_value):
            goto(fsm.state1)

    return interpolated_values

kps = Stream(KeyPoints())
vs = interpolate(kps)


class Verilog:
    class Module:
        def __init__(self):
            self.definitions = []
            self.io_signal_declarations = []
            self.signal_declarations = []
            self.submodule_declarations = []
            self.signal_assigns = []
            self.conditional_blocks = []
            self.sequential_block = []
        
    class File:
        def __init__(self):
            self.modules = []


def to_verilog(entity):
    verilog_file = Verilog.File()
    print(entity.to_verilog(verilog_file))

to_verilog(vs)
