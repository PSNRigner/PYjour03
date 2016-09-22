from pyrser import meta, grammar
from pyrser.parsing import node


@meta.add_method(node.Node)
def to_dxml(self):
    return "<.root" + self.to_dxml2(".root") + ">"


# noinspection PyProtectedMember
@meta.add_method(node.Node)
def to_dxml2(self, name, depth=1):
    result = ""
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
        result += ".idx"
    return result


def add_var(k, v, depth, index=-1, opt=""):
    result = ""
    result += indent(depth)
    result += "<"
    if k:
        result += k
    elif index != -1:
        result += (".idx __key = '" + opt + "'") if index == -2 else ".idx __value = " + str(index)
    tmp = {
        node.Node: lambda x: x.to_dxml2(k, depth + 1),
        type(None): lambda x: "/",
        str: lambda x: (" str = " if k or index != -1 else "") + "'" + str(x) + "'/",
        bool: lambda x: " bool = " + str(x) + "/",
        int: lambda x: " int = " + str(x) + "/",
        float: lambda x: " float = " + str(x) + "/",
        bytes: lambda x: blob(x, depth, k),
        set: lambda x: add_set(x, depth, k),
        dict: lambda x: add_dict(x, depth, k),
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
        tmp = hex(b[i])[2:].upper()
        if len(tmp) == 1:
            tmp = "0" + tmp
        result += tmp
        if i < len(b) - 1:
            result += " "
        i += 1
    result += "\n"
    result += indent(depth)
    result += "</" + name if name else "</.idx"
    return result


def add_set(s, depth, name):
    result = " type = set>\n"
    s = sorted(s)
    for i in s:
        result += add_var(None, i, depth + 1)
    result += indent(depth)
    result += "</" + name if name else "</.idx"
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


def add_dict(d, depth, name):
    result = " type = dict>\n"
    j = 0
    for i in sorted(d.items()):
        result += add_var(None, i[1], depth + 1, -2, i[0])
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


# noinspection PyPep8Naming
class dxmlParser(grammar.Grammar):
    entry = "Xml"
    grammar = """
    Xml = [ Object:o #finish(_,o) eof ]
    Object = [ [ None | Single | Block ]:>_ ]
    None = [ '<' FieldName:f "/>" #add_none(_,f) ]
    Single = [ '<' FieldName:f [ Type:t ]? '=' Value:v #add_single(_,f,t,v) "/>" ]
    Block = [ '<' FieldName:f Type:t '>' [ Object:o #add_child(_,o) ]* "</" FieldName '>' #add_block(_,f,t) ]
    FieldName = [ [ '.' ]? id ]
    Type = [ [ "type" "=" id ] | [ id ] ]
    Value = [ id:>_ | Float:>_ | num:>_ | String:>_ ]
    String = [ [ "'" ]? [ [ [ 'a'..'z' ] | [ 'A'..'Z' ] | [ '0'..'9' ] | [ ' ' ] | [ '_' ] ]+ ]:>_ [ "'" ]? ]
    Float = [ [ [ [ '0'..'9' ] | [ '.' ] | [ '-' ] | [ '+' ] | [ 'e' ] ]+ ] ]
    """


@meta.hook(dxmlParser)
def debug(self, arg):
    print(">> ", self.value(arg))
    return True


# noinspection PyUnusedLocal
@meta.hook(dxmlParser)
def finish(self, ast, o):
    for i in o.children:
        k = i.val[0].rstrip()
        v = i.val[1]
        if isinstance(v, node.Node):
            recur_node(i)
            v = i
        setattr(ast, k, v)
    return True


def recur_node(o):
    if hasattr(o, 'children'):
        for i in o.children:
            k = i.val[0].rstrip()
            v = i.val[1]
            if type(v) == node.Node:
                recur_node(v)
            setattr(o, k, v)


@meta.hook(dxmlParser)
def add_single(self, ast, f, t, v):
    fv = self.value(f)
    tv = self.value(t)
    vv = self.value(v)
    vv = vv.rstrip().strip("'")
    tmp = {
        "str": lambda x: x,
        "int": lambda x: int(x),
        "float": lambda x: float(x),
        "bool": lambda x: bool(x)
    }.get(tv)(vv)
    ast.val = fv, tmp
    return True


@meta.hook(dxmlParser)
def add_none(self, ast, f):
    fv = self.value(f)
    ast.val = fv, None
    return True


# noinspection PyUnusedLocal
@meta.hook(dxmlParser)
def add_child(self, ast, o):
    if hasattr(ast, 'children'):
        ast.children.append(o)
    else:
        ast.children = [o]
    return True


@meta.hook(dxmlParser)
def add_block(self, ast, f, t):
    fv = self.value(f)
    tv = self.value(t)
    if tv.startswith("type="):
        tv = tv[5:]
    if tv.startswith("type ="):
        tv = tv[6:]
    if tv[0] == ' ':
        tv = tv[1:]
    tmp = {
        "list": lambda: list(),
        "set": lambda: set(),
        "dict": lambda: dict(),
        "object": lambda: node.Node()
    }[tv]()
    ast.val = fv, tmp
    return True
