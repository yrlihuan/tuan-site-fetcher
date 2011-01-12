import struct

JPEG_INIT_BITS = '\xff\xd8'
PNG_INIT_BITS = ''



class Image(object):
    INIT_TYPE_TABLE = {'JPEG' : '\xff\xd8',
                       'PNG' : '\x89\x50\x4e\x47\x0d\x0a\x1a\x0a',
                       'BMP' : '\x42\x4d'}

    def __init__(self, file_obj):
        self.buf = AutoFetchBuffer(file_obj)
        self._type = None

    def type(self):
        if not self._type:
            for t in self.INIT_TYPE_TABLE:
                signiture = self.INIT_TYPE_TABLE[t]
                siglen = len(signiture)

                if self.buf.getrange(0, siglen) == signiture:
                    self._type = t
                    break
                
            if not self._type:
                self._type = 'UNKNOWN'

        return self._type
    
    def dimensions(self):
        t = self.type()
        width = -1
        height = -1

        if t == 'BMP':
            # ref: http://en.wikipedia.org/wiki/BMP_file_format
            width, height = struct.unpack('<ii', self.buf.getrange(18, 26))
        elif t == 'PNG':
            # ref: http://www.fileformat.info/format/png/corion.htm
            IHDR_header = 'IHDR'
            header_len = len(IHDR_header)
            match_len = 0
            match_start = -1
            ind = 0
            for byte in self.buf:
                if byte == IHDR_header[match_len]:
                    match_start = ind - match_len
                    match_len += 1
                elif byte == IHDR_header[0]:
                    match_start = ind
                    match_len = 1
                else:
                    match_start = -1
                    match_len = 0

                if match_len == header_len:
                    break

                ind += 1

            if match_len == header_len:
                width, height = struct.unpack('>ii', self.buf.getrange(match_start+match_len, match_start+match_len+8))
        elif t == 'JPEG':
            # ref: http://wiki.tcl.tk/757
            pos = 2 # skip the first ffd0 marker
            sof_markers = ['\xc0','\xc1','\xc2','\xc3','\xc4','\xc5','\xc6','\xc7','\xc8','\xc9','\xca','\xcb','\xcc','\xcd','\xce','\xcf']

            try:
               while True:
                   if self.buf.get(pos) != '\xff': # according to the markers definitions, it must start with 0xff
                       break

                   if self.buf.get(pos + 1) in sof_markers: # Find a SOF marker, extract dimension info
                       height, width = struct.unpack('>HH', self.buf.getrange(pos+5, pos+9))
                       break
                   else: # Not a SOF marker, skip the section
                       marker_len = struct.unpack('>H', self.buf.getrange(pos+2, pos+4))
                       pos += 2 + marker_len[0]
            except IndexError, ex:
               print ex

        return width, height
            
class AutoFetchBuffer(object):
    GROW_SIZE = [256, 256, 512, 1024, 2048, 4096, 8192, 20480, 40960, 81920]

    def __init__(self, file_obj):
        self._file = file_obj
        self._buf = ''
        self._buflen = 0
        self._grow = 0
        self._eof = False

    def get(self, ind):
        self._ensure_size(ind)
        return self._buf[ind]


    def getrange(self, i, j):
        if i < 0 or j < 0 or i > j:
            raise IndexError()

        self._ensure_size(j)
        return self._buf[i:j]

    def __iter__(self):
        pos = 0

        while True:
            self._ensure_size(pos)

            if pos < self._buflen:
                yield self._buf[pos]
                pos += 1
            else:
                return

    def _ensure_size(self, p):
        while p >= self._buflen and not self._eof:
            if self._grow < len(self.GROW_SIZE):
                grow_size = self.GROW_SIZE[self._grow]
            else:
                grow_size = self.GROW_SIZE[-1]

            new_chunk = self._file.read(grow_size)

            self._buf += new_chunk
            self._grow += 1
            self._buflen = len(self._buf)
            self._eof = len(new_chunk) != grow_size

