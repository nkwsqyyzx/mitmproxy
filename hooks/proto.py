import json

from google.protobuf import descriptor
from google.protobuf.message import Message

_TYPE_DOUBLE = 1
_TYPE_FLOAT = 2
_TYPE_INT64 = 3
_TYPE_UINT64 = 4
_TYPE_INT32 = 5
_TYPE_FIXED64 = 6
_TYPE_FIXED32 = 7
_TYPE_BOOL = 8
_TYPE_STRING = 9
_TYPE_GROUP = 10
_TYPE_MESSAGE = 11
_TYPE_BYTES = 12
_TYPE_UINT32 = 13
_TYPE_ENUM = 14
_TYPE_SFIXED32 = 15
_TYPE_SFIXED64 = 16
_TYPE_SINT32 = 17
_TYPE_SINT64 = 18

_INT_TYPE = [_TYPE_INT64, _TYPE_UINT64, _TYPE_INT32, _TYPE_FIXED64, _TYPE_FIXED32, _TYPE_UINT32, _TYPE_ENUM,
             _TYPE_SFIXED32, _TYPE_SFIXED64, _TYPE_SINT32, _TYPE_SINT64, _TYPE_BOOL]


def json2proto(root, msg):
    if root is None or (not msg):
        return root
    name_type = [(i.name, i.label, i.type) for i in root.DESCRIPTOR.fields]
    for (name, label, msg_type) in name_type:
        if label == descriptor.FieldDescriptor.LABEL_REPEATED:
            values = msg.get(name, [])
            if values:
                arr = getattr(root, name)
                if msg_type == _TYPE_MESSAGE:
                    for i in values:
                        new = arr.add()
                        json2proto(new, i)
                else:
                    arr.extend(values)
            continue
        if msg_type == _TYPE_MESSAGE:
            json2proto(getattr(root, name), msg.get(name))
        elif msg_type in [_TYPE_DOUBLE, _TYPE_FLOAT]:
            setattr(root, name, float(msg.get(name) or '0'))
        elif msg_type in _INT_TYPE:
            v = msg.get(name)
            if isinstance(v, str):
                v = str2int(v)
            try:
                setattr(root, name, int(v or 0))
            except ValueError:
                x = int(v) & 0x7FFFFFFF
                setattr(root, name, x)
        elif msg_type == _TYPE_STRING:
            z = msg.get(name, u'')
            if isinstance(z, dict):
                z = json.dumps(z, ensure_ascii=False)
            else:
                z = str(z)
            sz = z
            try:
                setattr(root, name, sz.encode('utf8'))
            except ValueError:
                sz = str(sz)
                setattr(root, name, sz.encode('utf8'))
        else:
            raise Exception('Unknown message type {0} for field {1}'.format(msg_type, name))
    return root


def proto2json(root):
    msg = {}
    if not root:
        return msg

    if not isinstance(root, Message):
        return root

    name_type = [(i.name, i.label, i.type) for i in root.DESCRIPTOR.fields]
    for (name, label, msg_type) in name_type:
        if label == descriptor.FieldDescriptor.LABEL_REPEATED:
            arr = getattr(root, name)
            if arr:
                msg[name] = [proto2json(i) for i in arr]
            continue
        if msg_type == _TYPE_MESSAGE:
            v = getattr(root, name)
            if v:
                msg[name] = proto2json(v)
        elif msg_type in [_TYPE_DOUBLE, _TYPE_FLOAT]:
            msg[name] = float(getattr(root, name))
        elif msg_type in _INT_TYPE:
            msg[name] = int(getattr(root, name))
        elif msg_type == _TYPE_STRING:
            msg[name] = str(getattr(root, name))
        else:
            raise Exception('Unknown message type {0} for field {1}'.format(msg_type, name))

    return msg


def format_function(cls, f):
    full_class_name = cls.__module__ + '.' + cls.__class__.__name__
    return '{0}:{1}'.format(full_class_name, f.__name__)



