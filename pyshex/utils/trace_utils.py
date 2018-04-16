from typing import Callable

from ShExJSG.ShExJ import NodeConstraint
from pyjsg.jsglib import jsg

from pyshex.parse_tree.parse_node import ParseNode
from pyshex.shape_expressions_language.p5_context import Context, DebugContext
from pyshex.shapemap_structure_and_language.p1_notation_and_terminology import RDFGraph, Node

# TODO: factor out common code below.  Differences are minor

def trace_satisfies(newline: bool=True, skip_trace: Callable[[jsg.JSGObject], bool]=lambda _: False):
    def e(f: Callable[[Context, Node, jsg.JSGObject, DebugContext], bool]):
        def wrapper(cntxt: Context, n: Node, expr: jsg.JSGObject) -> bool:
            parent_parse_node = cntxt.current_node
            cntxt.current_node = ParseNode(f, expr, n)
            parent_parse_node.nodes.append(cntxt.current_node)
            c = cntxt.debug_context
            c.splus()
            if c.debug and not skip_trace(expr):
                print(c.i(0, f'--> {f.__name__} {c.d()} node: {n}'), end=None if newline else '')
            rval = f(cntxt, n, expr, c)
            if c.debug and not skip_trace(expr):
                print(c.i(0, f'<-- {f.__name__} {c.d()} node: {n}: {rval}'))
            c.sminus()
            cntxt.current_node.result = rval
            cntxt.current_node = parent_parse_node
            return rval
        return wrapper
    return e


def trace_matches(newline: bool=True):
    def e(f: Callable[[Context, RDFGraph, jsg.JSGObject, DebugContext], bool]):
        def wrapper(cntxt: Context, T: RDFGraph, expr: jsg.JSGObject) -> bool:
            parent_parse_node = cntxt.current_node
            cntxt.current_node = ParseNode(f, expr, T)
            parent_parse_node.nodes.append(cntxt.current_node)
            c = cntxt.debug_context
            c.splus()
            if c.debug:
                print(c.i(0, f'--> {f.__name__} {c.d()}'), end=None if newline else '')
            rval = f(cntxt, T, expr, c)
            if c.debug:
                print(c.i(0, f'<-- {f.__name__} {c.d()} {rval}'))
            c.sminus()
            cntxt.current_node.result = rval
            cntxt.current_node = parent_parse_node
            return rval
        return wrapper
    return e


def trace_matches_tripleconstraint(newline: bool=True):
    def e(f: Callable[[Context, Node, jsg.JSGObject, DebugContext], bool]):
        def wrapper(cntxt: Context, n: Node, expr: jsg.JSGObject) -> bool:
            c = cntxt.debug_context
            c.splus()
            if c.debug:
                print(c.i(0, f'--> {f.__name__} {c.d()}'), end=None if newline else '')
            rval = f(cntxt, n, expr, c)
            if c.debug:
                print(c.i(0, f'<-- {f.__name__} {c.d()} {rval}'))
            c.sminus()
            return rval
        return wrapper
    return e