import re

from mitmproxy.net.http import headers


def decode(hdrs, content):
    """
        Takes a multipart boundary encoded string and returns list of (key, value) tuples.
    """
    v = hdrs.get("content-type")
    if v:
        v = headers.parse_content_type(v)
        if not v:
            return []
        try:
            boundary = v[2]["boundary"].encode("ascii")
        except (KeyError, UnicodeError):
            return []

        rx = re.compile(br'\bname="([^"]+)"')
        r = []

        for i in content.split(b"--" + boundary):
            parts = i.split(b'\r\n\r\n', 2)
            if len(parts) > 1 and parts[0][0:2] != b"--":
                match = rx.search(parts[0])
                if match:
                    key = match.group(1)
                    value = parts[1][0:len(parts[1])-2] # Remove last \r\n
                    r.append((key, value))
        return r
    return []
