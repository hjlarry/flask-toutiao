import struct
import time
import os
import random
import threading
import binascii


class ObjectId:
    _inc = random.randint(0, 0xFFFFFF)
    _inc_lock = threading.Lock()


def generate_id():
    oid = struct.pack(">i", int(time.time()))
    oid += struct.pack(">H", os.getpid() % 0xFFFF)
    with ObjectId._inc_lock:
        oid += struct.pack(">i", ObjectId._inc)[2:4]
        ObjectId._inc = (ObjectId._inc + 1) % 0xFFFFFF
    return binascii.hexlify(oid).decode("utf-8")


class Empty:
    def __call__(self, *a, **kw):
        return empty

    def __nonzero__(self):
        return False

    def __contains__(self, item):
        return False

    def __repr__(self):
        return "<Empty Object>"

    def __str__(self):
        return ""

    def __eq__(self, v):
        return isinstance(v, Empty)

    def __getattr__(self, name):
        if not name.startswith("__"):
            return empty
        raise AttributeError(name)

    def __len__(self):
        return 0

    def __getitem__(self, key):
        return empty

    def __setitem__(self, key, value):
        pass

    def __delitem__(self, key):
        pass

    def __iter__(self):
        return self

    def __next__(self):
        raise StopIteration

    def next(self):
        raise StopIteration


empty = Empty()
