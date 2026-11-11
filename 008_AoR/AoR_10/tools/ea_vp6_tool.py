"""EA VP6 (.vp6) helpers: strip audio chunks / replace video frames keeping the original chunk order."""
import struct, sys

def chunks(data):
    pos = 0
    while pos + 8 <= len(data):
        tag, size = data[pos:pos+4], struct.unpack('<I', data[pos+4:pos+8])[0]
        yield tag, data[pos+8:pos+size]
        pos += size

def video_frames(data):
    return [b for t, b in chunks(data) if t in (b'MV0K', b'MV0F')]

def strip_audio(src, dst):
    data = open(src, 'rb').read()
    out = bytearray()
    for t, b in chunks(data):
        if t in (b'MVhd', b'MV0K', b'MV0F'):
            out += t + struct.pack('<I', len(b) + 8) + b
    open(dst, 'wb').write(out)

def replace_video(orig, new, dst):
    """Original chunk sequence (audio included), each MV0F payload swapped for the new encode's frame i."""
    o = open(orig, 'rb').read()
    n = [(t, b) for t, b in chunks(open(new, 'rb').read()) if t in (b'MV0K', b'MV0F')]
    out, i = bytearray(), 0
    for t, b in chunks(o):
        if t == b'MVhd':
            b = bytearray(b); b[8:12] = struct.pack('<I', len(n)); b[12:16] = struct.pack('<I', max(len(x) for _, x in n))
        elif t in (b'MV0K', b'MV0F'):
            if i >= len(n):  # original has more frames (its last one is broken): drop the rest
                continue
            t, b = n[i]; i += 1
        out += t + struct.pack('<I', len(b) + 8) + bytes(b)
    for t, b in n[i:]:  # new encode has more frames than the original: append them
        out += t + struct.pack('<I', len(b) + 8) + b
    print('frames: original', len(video_frames(o)), 'new', len(n))
    open(dst, 'wb').write(out)

if __name__ == '__main__':
    {'strip': strip_audio, 'replace': replace_video}[sys.argv[1]](*sys.argv[2:])
