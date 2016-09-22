from pyrser import meta
from pyrser.parsing import node


@meta.add_method(node.Node)
def to_dxml(self):
    return self.to_dxml2(None) + ">"


# noinspection PyProtectedMember
@meta.add_method(node.Node)
def to_dxml2(self, name, depth=1):
    result = ""
    if not name:
        result += "<.root"
    result += " type = object>\n"
    var = sorted(vars(self).items())
    for k in var:
        v = k[1]
        k = k[0]
        result += add_var(k, v, depth)
    result += indent(depth - 1)
    result += "</"
    if name:
        result += name
    else:
        result += ".root"
    return result


def add_var(k, v, depth, index=-1):
    result = ""
    result += indent(depth)
    result += "<"
    if k:
        result += k
    elif index != -1:
        result += ".idx __value = " + str(index)
    tmp = {
        node.Node: lambda x: x.to_dxml2(k, depth + 1),
        type(None): lambda x: "/",
        str: lambda x: (" str = " if k or index != -1 else "") + "'" + str(x) + "'/",
        bool: lambda x: " bool = " + str(x) + "/",
        int: lambda x: " int = " + str(x) + "/",
        float: lambda x: " float = " + str(x) + "/",
        bytes: lambda x: blob(x, depth, k),
        set: lambda x: add_set(x, depth, k),
        # dict: lambda x: "",
        list: lambda x: add_list(x, depth, k),
        # type('X'): lambda x: ""
    }.get(type(v), lambda x: "")(v)
    result += tmp + ">\n"
    return result


def blob(b, depth, name):
    result = " type = blob>\n"
    result += indent(depth + 1)
    i = 0
    while i < len(b):
        result += hex(b[i])[2:].upper()
        if i < len(b) - 1:
            result += " "
        i += 1
    result += "\n"
    result += indent(depth)
    result += "</" + name if name else ".idx"
    return result


def add_set(s, depth, name):
    result = " type = set>\n"
    s = sorted(s)
    for i in s:
        result += add_var(None, i, depth + 1)
    result += indent(depth)
    result += "</" + name if name else ".idx"
    return result


def add_list(l, depth, name):
    result = " type = list>\n"
    j = 0
    for i in l:
        result += add_var(None, i, depth + 1, j)
        j += 1
    result += indent(depth)
    result += "</" + name if name else "</.idx"
    return result


def indent(depth):
    i = 0
    result = ""
    while i < depth:
        result += "\t"
        i += 1
    return result
