from hashlib import sha1
from urllib.parse import quote, unquote_plus
import os


def url_encode(s):
    return quote(s.encode('utf-8'))


def url_decode(s):
    return unquote_plus(str(s)).decode('utf-8')


def get_content_length(file):
    if hasattr(file, 'name') and os.path.isfile(file.name):
        return os.path.getsize(file.name)
    raise Exception('Content-Length could not be automatically determined.')


def get_part_ranges(content_length, part_size):
    next_offest = 0
    while content_length > 0:
        if content_length < part_size:
            part_size = content_length
        yield (next_offest, part_size)
        next_offest += part_size
        content_length -= part_size


class StreamWithHashProgress:
    """
    Wraps a file-like object (read-only), hashes on-the-fly, and
    updates a progress_listener as data is read.
    """

    def __init__(self, stream, progress_listener=None):
        self.stream = stream
        self.progress_listener = progress_listener
        self.bytes_completed = 0
        self.digest = sha1()
        self.hash = None
        self.hash_read = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.stream.__exit__(exc_type, exc_val, exc_tb)

    def read(self, size=None):
        data = b''
        if self.hash is None:
            # Read some bytes from stream
            if size is None:
                data = self.stream.read()
            else:
                data = self.stream.read(size)

            # Update hash
            self.digest.update(data)

            # Check for end of stream
            if size is None or len(data) < size:
                self.hash = self.digest.hexdigest()
                if size is not None:
                    size -= len(data)

            # Update progress listener
            self._update(len(data))

        else:
            # The end of stream was reached, return hash now
            size = size or len(self.hash)
            data += str.encode(self.hash[self.hash_read:self.hash_read + size])
            self.hash_read += size

        return data

    def _update(self, delta):
        self.bytes_completed += delta
        if self.progress_listener is not None:
            self.progress_listener(self.bytes_completed)

    def get_hash(self):
        return self.hash

    def hash_size(self):
        return self.digest.digest_size * 2
