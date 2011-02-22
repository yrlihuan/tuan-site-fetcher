import pickle
import bz2
import hashlib

SIGFILE = 'rpc/signature'

class CorruptedError(Exception):
    pass

class MessageBase(object):
    SIGNATURE = open(SIGFILE, 'r').read()

    def __init__(self, f, t):
        self._from = f
        self._to = t

    @classmethod
    def serialize(cls, obj):
        if not isinstance(obj, cls):
            raise TypeError('Can not serialize type %s' % str(type(obj)))

        payload = bz2.compress(pickle.dumps(obj))
        digest = cls.generatedigest(payload)

        return digest + payload

    @classmethod
    def deserialize(cls, buf):
        digest = buf[0:16]
        payload = buf[16:]

        if not cls.verifydigest(payload, digest):
            raise CorruptedError()

        obj = pickle.loads(bz2.decompress(payload))

        if not isinstance(obj, cls):
            raise TypeError('deserialized object (type %s) is not of type %s' % (str(type(obj)), str(cls)))

        return obj

    @classmethod
    def generatedigest(cls, s):
        md5 = hashlib.md5()
        md5.update(cls.SIGNATURE)
        md5.update(s)
        return md5.digest()

    @classmethod
    def verifydigest(cls, s, digest):
        return cls.generatedigest(s) == digest

class Request(MessageBase):
    def __init__(self, f, t, service, method, *args, **params):
        self.service = service
        self.method = method
        self.args = args
        self.params = params

        MessageBase.__init__(self, f, t)
    
class Response(MessageBase):
    def __init__(self, f, t, return_value, error=None, callstack=None):
        self.return_value = return_value
        self.exception = error
        self.callstack = callstack

        MessageBase.__init__(self, f, t)
