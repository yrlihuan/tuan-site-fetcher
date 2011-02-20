import pickle
import bz2

class MessageBase(object):
    def __init__(self, f, t):
        self._from = f
        self._to = t

    @classmethod
    def serialize(cls, obj):
        if not isinstance(obj, cls):
            raise TypeError('Can not serialize type %s' % str(type(obj)))

        return bz2.compress(pickle.dumps(obj))

    @classmethod
    def deserialize(cls, buf):
        obj = pickle.loads(bz2.decompress(buf))

        if not isinstance(obj, cls):
            raise TypeError('deserialized object (type %s) is not of type %s' % (str(type(obj)), str(cls)))

        return obj

class Request(MessageBase):
    def __init__(self, f, t, service, method, **params):
        self.service = service
        self.method = method
        self.params = params

        MessageBase.__init__(self, f, t)
    
class Response(MessageBase):
    def __init__(self, f, t, return_value, error=None, callstack=None):
        self.return_value = return_value
        self.exception = error
        self.callstack = callstack

        MessageBase.__init__(self, f, t)
