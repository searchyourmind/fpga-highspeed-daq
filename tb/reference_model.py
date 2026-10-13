"""Independent mathematical oracle; no DUT state or model memory is consulted."""
def records(count, frame_len, gain):
    frame_len = max(1, frame_len)
    result = []
    for n in range(count):
        raw = (73*n+19) % 65536
        sample = min(raw*gain,65535)
        last = int((n+1) % frame_len == 0 or n == count-1)
        frame = (n // frame_len) % 32768
        result.append(sample | n<<16 | last<<48 | frame<<49)
    return result
