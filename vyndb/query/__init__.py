from query.lexer import tokenize, LexerError
from query.parser import parse, ParseError
from query.planner import Planner
from query.executor import Executor, ExecutionError


def run_query(sql, catalog, pool, storage):
    ast  = parse(sql)
    plan = Planner(catalog).plan(ast)
    return Executor(catalog, pool, storage).execute(plan)


__all__ = [
    'tokenize', 'parse', 'Planner', 'Executor',
    'run_query', 'LexerError', 'ParseError', 'ExecutionError',
]