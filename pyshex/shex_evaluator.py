from typing import Optional, Union, List, NamedTuple, Iterable

from ShExJSG import ShExJ, Schema, ShExC
from rdflib import Graph, URIRef, Namespace

from pyshex.shape_expressions_language.p5_2_validation_definition import isValid
from pyshex.shape_expressions_language.p5_context import Context
from pyshex.shapemap_structure_and_language.p3_shapemap_structure import FixedShapeMap, ShapeAssociation, START
from pyshex.utils.schema_loader import SchemaLoader


class EvaluationResult(NamedTuple):
    result: bool
    focus: URIRef
    start: URIRef
    reason: str


# Handy types
URI = Union[str, URIRef]
URILIST = List[URI]
URIPARM = Union[str, URIRef, URILIST]


class ShExEvaluator:
    """ Shape Expressions Evaluator """

    def __init__(self,
                 rdf: Optional[Union[str, Graph]] = None,
                 schema: Optional[Union[str, ShExJ.Schema]] = None,
                 focus: Optional[URIPARM] = None,
                 start: Optional[URIPARM] = None,
                 rdf_format: str = "turtle",
                 debug: bool = False) -> None:
        """ Evaluator constructor.  All of the parameters below can be set in the constructor or at runtime

        :param rdf: RDF string, file name, URL or Graph for evaluation.
        :param schema: ShEx Schema to evaluate. Can be ShExC, ShExJ or a pre-parsed schema
        :param focus: focus node(s).  If absent, all non-BNode subjects in the graph are evaluated
        :param start: start node(s). If absent, the START node in the schema is used
        :param rdf_format: format for RDF. Default: "Turtle"
        :param debug: emit semi-helpful debug information
        """
        self.rdf_format = rdf_format
        self.g = None
        self.rdf = rdf
        self._schema = None
        self.schema = schema
        self._focus = None
        self.focus = focus
        self._start = None
        self.start = start
        self.debug = debug

    @property
    def rdf(self) -> str:
        """

        :return: The rendering of whatever RDF is currently being evaluated
        """
        return self.g.serialize(format=self.rdf_format).decode()

    @rdf.setter
    def rdf(self, rdf: Optional[Union[str, Graph]]) -> None:
        """ Set the RDF DataSet to be evaulated.  If ``rdf`` is a string, the presence of a return is the
        indicator that it is text instead of a location.

        :param rdf: File name, URL, representation of rdflib Graph
        """
        if isinstance(rdf, Graph):
            self.g = rdf
        else:
            self.g = Graph()
            if isinstance(rdf, str):
                if '\n' in rdf or '\r' in rdf:
                    self.g.parse(data=rdf, format=self.rdf_format)
                elif ':' in rdf:
                    self.g.parse(location=rdf, format=self.rdf_format)
                else:
                    self.g.parse(source=rdf, format=self.rdf_format)

    @property
    def schema(self) -> Optional[str]:
        """

        :return: The ShExC representation of the schema if one is supplied
        """
        return str(ShExC(self._schema)) if self._schema else None

    @schema.setter
    def schema(self, shex: Optional[Union[str, ShExJ.Schema]]) -> None:
        """ Set the schema to be used.  Schema can either be a ShExC or ShExJ string or a pre-parsed schema.

        :param shex:  Schema
        """
        self._schema = None if shex is None else SchemaLoader().loads(shex)

    @property
    def focus(self) -> Optional[List[URIRef]]:
        """
        :return: The list of focus nodes (if any)
        """
        return self._focus

    @property
    def foci(self) -> List[URIRef]:
        """

        :return: The current set of focus nodes
        """
        return self._focus if self._focus else sorted([s for s in set(self.g.subjects()) if isinstance(s, URIRef)])

    @focus.setter
    def focus(self, focus: Optional[URIPARM]) -> None:
        """ Set the focus node(s).  If no focus node is specified, the evaluation will occur for all non-BNode
        graph subjects.  Otherwise it can be a string, a URIRef or a list of string/URIRef combinations

        :param focus: None if focus should be all URIRefs in the graph otherwise a URI or list of URI's
        """
        if focus is None:
            self._focus = None
        else:
            if not isinstance(focus, Iterable) or isinstance(focus, (Namespace, URIRef)):
                focus = [focus]
            self._focus = [f if isinstance(f, URIRef) else URIRef(str(f)) for f in focus]

    @property
    def start(self) -> Optional[List[URIRef]]:
        """

        :return: The schema start node(s)
        """
        return self._start

    @start.setter
    def start(self, start: Optional[URIPARM]) -> None:
        if start is None:
            self._start = [START]
        else:
            if not isinstance(start, Iterable) or isinstance(start, (Namespace, URIRef)):
                start = [start]
            self._start = [s if isinstance(s, URIRef) else URIRef(str(s)) for s in start]

    def evaluate(self,
                 rdf: Optional[Union[str, Graph]] = None,
                 shex: Optional[Union[str, ShExJ.Schema]] = None,
                 focus: Optional[URIPARM] = None,
                 start: Optional[URIPARM] = None,
                 rdf_format: Optional[str] = None,
                 debug: Optional[bool] = None) -> List[EvaluationResult]:
        if rdf or shex or focus or start:
            evaluator = ShExEvaluator(rdf, shex, focus, start, rdf_format)
            if not rdf:
                evaluator.g = self.g
            if not shex:
                evaluator._schema = self._schema
            if not focus:
                evaluator._focus = self._focus
            if not start:
                evaluator._start = self._start
        else:
            evaluator = self

        cntxt = Context(evaluator.g, evaluator._schema)
        cntxt.debug_context.trace_satisfies = cntxt.debug_context.trace_matches = \
            cntxt.debug_context.trace_nodeSatisfies = debug if debug is not None else self.debug

        rval = []
        for start in evaluator.start:
            for focus in evaluator.foci:
                map_ = FixedShapeMap()
                map_.add(ShapeAssociation(focus, start))
                rval.append(EvaluationResult(isValid(cntxt, map_), focus, start, ""))
        return rval