import struct, sys
def entries(p):
    d = open(p, 'rb').read()
    n = struct.unpack('>I', d[8:12])[0]; pos = 16; out = []
    for _ in range(n):
        off, size = struct.unpack('>II', d[pos:pos + 8]); pos += 8
        e = d.index(b'\0', pos); name = d[pos:e].decode('latin1'); pos = e + 1
        out.append((name, off, size))
    return d, out
if __name__ == '__main__':
    for p in sys.argv[1:]:
        _, es = entries(p)
        for name, off, size in es: print(p.split('/')[-1], name, size)
