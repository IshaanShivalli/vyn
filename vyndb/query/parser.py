from query.lexer import tokenize, TokenType, LexerError


class ParseError(Exception):
    pass


class Node:
    pass


class SelectNode(Node):
    def __init__(self, columns, from_table, joins, where,
                 group_by, having, order_by, limit, offset, distinct):
        self.columns   = columns
        self.from_table= from_table
        self.joins     = joins
        self.where     = where
        self.group_by  = group_by
        self.having    = having
        self.order_by  = order_by
        self.limit     = limit
        self.offset    = offset
        self.distinct  = distinct


class InsertNode(Node):
    def __init__(self, table, columns, values):
        self.table   = table
        self.columns = columns
        self.values  = values


class UpdateNode(Node):
    def __init__(self, table, assignments, where):
        self.table       = table
        self.assignments = assignments
        self.where       = where


class DeleteNode(Node):
    def __init__(self, table, where):
        self.table = table
        self.where = where


class CreateTableNode(Node):
    def __init__(self, table, columns, constraints):
        self.table       = table
        self.columns     = columns
        self.constraints = constraints


class DropTableNode(Node):
    def __init__(self, table):
        self.table = table


class CreateIndexNode(Node):
    def __init__(self, name, table, column, unique):
        self.name   = name
        self.table  = table
        self.column = column
        self.unique = unique


class DropIndexNode(Node):
    def __init__(self, name, table):
        self.name  = name
        self.table = table


class AlterTableNode(Node):
    def __init__(self, table, operation, payload):
        self.table     = table
        self.operation = operation
        self.payload   = payload


class BeginNode(Node):
    pass


class CommitNode(Node):
    pass


class RollbackNode(Node):
    def __init__(self, savepoint=None):
        self.savepoint = savepoint


class SavepointNode(Node):
    def __init__(self, name):
        self.name = name


class ExplainNode(Node):
    def __init__(self, inner):
        self.inner = inner


class TruncateNode(Node):
    def __init__(self, table):
        self.table = table


class JoinNode(Node):
    def __init__(self, join_type, table, alias, condition):
        self.join_type = join_type
        self.table     = table
        self.alias     = alias
        self.condition = condition


class BinaryOp(Node):
    def __init__(self, op, left, right):
        self.op    = op
        self.left  = left
        self.right = right


class UnaryOp(Node):
    def __init__(self, op, operand):
        self.op      = op
        self.operand = operand


class Column(Node):
    def __init__(self, name, table=None, alias=None):
        self.name  = name
        self.table = table
        self.alias = alias


class Star(Node):
    def __init__(self, table=None):
        self.table = table


class Literal(Node):
    def __init__(self, value):
        self.value = value


class FunctionCall(Node):
    def __init__(self, name, args, distinct=False):
        self.name     = name
        self.args     = args
        self.distinct = distinct


class SubqueryNode(Node):
    def __init__(self, select_node):
        self.select_node = select_node


class CaseNode(Node):
    def __init__(self, whens, else_expr):
        self.whens     = whens
        self.else_expr = else_expr


class InNode(Node):
    def __init__(self, expr, values, negated):
        self.expr    = expr
        self.values  = values
        self.negated = negated


class BetweenNode(Node):
    def __init__(self, expr, low, high, negated):
        self.expr    = expr
        self.low     = low
        self.high    = high
        self.negated = negated


class IsNullNode(Node):
    def __init__(self, expr, negated):
        self.expr    = expr
        self.negated = negated


class LikeNode(Node):
    def __init__(self, expr, pattern, negated):
        self.expr    = expr
        self.pattern = pattern
        self.negated = negated


class OrderByItem(Node):
    def __init__(self, expr, descending):
        self.expr       = expr
        self.descending = descending


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos    = 0

    def _peek(self, ahead=0):
        p = self.pos + ahead
        if p < len(self.tokens):
            return self.tokens[p]
        return self.tokens[-1]

    def _advance(self):
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def _expect(self, ttype, value=None):
        tok = self._advance()
        if tok.ttype != ttype:
            raise ParseError(f"Expected {ttype.name} but got {tok.ttype.name} ({tok.value!r}) at pos {tok.pos}")
        if value is not None and tok.value != value:
            raise ParseError(f"Expected '{value}' but got '{tok.value}' at pos {tok.pos}")
        return tok

    def _match(self, ttype, value=None):
        tok = self._peek()
        if tok.ttype != ttype:
            return False
        if value is not None and tok.value != value:
            return False
        return True

    def _match_keyword(self, *words):
        for i, w in enumerate(words):
            t = self._peek(i)
            if t.ttype != TokenType.KEYWORD or t.value != w:
                return False
        return True

    def _consume_keyword(self, *words):
        for w in words:
            self._expect(TokenType.KEYWORD, w)

    def parse(self):
        node = self._parse_statement()
        if self._match(TokenType.SEMICOLON):
            self._advance()
        return node

    def _parse_statement(self):
        tok = self._peek()
        if tok.ttype == TokenType.KEYWORD:
            kw = tok.value
            if kw == 'SELECT':    return self._parse_select()
            if kw == 'INSERT':    return self._parse_insert()
            if kw == 'UPDATE':    return self._parse_update()
            if kw == 'DELETE':    return self._parse_delete()
            if kw == 'CREATE':    return self._parse_create()
            if kw == 'DROP':      return self._parse_drop()
            if kw == 'ALTER':     return self._parse_alter()
            if kw == 'BEGIN':     self._advance(); return BeginNode()
            if kw == 'COMMIT':    self._advance(); return CommitNode()
            if kw == 'ROLLBACK':  return self._parse_rollback()
            if kw == 'SAVEPOINT': return self._parse_savepoint()
            if kw == 'EXPLAIN':   return self._parse_explain()
            if kw == 'TRUNCATE':  return self._parse_truncate()
        raise ParseError(f"Unexpected token {tok.value!r} at pos {tok.pos}")

    def _parse_select(self, subquery=False):
        self._consume_keyword('SELECT')
        distinct = False
        if self._match_keyword('DISTINCT'):
            self._advance()
            distinct = True
        columns = self._parse_select_columns()
        from_table = None
        alias      = None
        joins      = []
        if self._match_keyword('FROM'):
            self._advance()
            from_table, alias = self._parse_table_ref()
            joins = self._parse_joins()
        where    = self._parse_where()
        group_by = self._parse_group_by()
        having   = self._parse_having()
        order_by = self._parse_order_by()
        limit    = self._parse_limit()
        offset   = self._parse_offset()
        return SelectNode(columns, (from_table, alias), joins, where,
                          group_by, having, order_by, limit, offset, distinct)

    def _parse_select_columns(self):
        cols = []
        while True:
            cols.append(self._parse_select_expr())
            if not self._match(TokenType.COMMA):
                break
            self._advance()
        return cols

    def _parse_select_expr(self):
        if self._match(TokenType.STAR):
            self._advance()
            return Star()
        expr = self._parse_expr()
        alias = None
        if self._match_keyword('AS'):
            self._advance()
            alias = self._advance().value
        elif self._match(TokenType.IDENTIFIER):
            alias = self._advance().value
        if isinstance(expr, Column):
            expr.alias = alias
        return expr

    def _parse_table_ref(self):
        if self._match(TokenType.LPAREN):
            self._advance()
            sub = self._parse_select(subquery=True)
            self._expect(TokenType.RPAREN)
            alias = None
            if self._match_keyword('AS'):
                self._advance()
            if self._match(TokenType.IDENTIFIER):
                alias = self._advance().value
            return SubqueryNode(sub), alias
        name = self._expect(TokenType.IDENTIFIER).value
        alias = None
        if self._match_keyword('AS'):
            self._advance()
            alias = self._advance().value
        elif self._match(TokenType.IDENTIFIER):
            alias = self._advance().value
        return name, alias

    def _parse_joins(self):
        joins = []
        join_keywords = {'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS', 'NATURAL'}
        while self._peek().ttype == TokenType.KEYWORD and self._peek().value in join_keywords:
            join_type = self._advance().value
            if join_type != 'JOIN':
                if self._match_keyword('OUTER'):
                    self._advance()
                self._expect(TokenType.KEYWORD, 'JOIN')
            table, alias = self._parse_table_ref()
            condition = None
            if self._match_keyword('ON'):
                self._advance()
                condition = self._parse_expr()
            joins.append(JoinNode(join_type, table, alias, condition))
        return joins

    def _parse_where(self):
        if not self._match_keyword('WHERE'):
            return None
        self._advance()
        return self._parse_expr()

    def _parse_group_by(self):
        if not self._match_keyword('GROUP'):
            return None
        self._advance()
        self._expect(TokenType.KEYWORD, 'BY')
        items = [self._parse_expr()]
        while self._match(TokenType.COMMA):
            self._advance()
            items.append(self._parse_expr())
        return items

    def _parse_having(self):
        if not self._match_keyword('HAVING'):
            return None
        self._advance()
        return self._parse_expr()

    def _parse_order_by(self):
        if not self._match_keyword('ORDER'):
            return None
        self._advance()
        self._expect(TokenType.KEYWORD, 'BY')
        items = []
        while True:
            expr = self._parse_expr()
            desc = False
            if self._match_keyword('DESC'):
                self._advance()
                desc = True
            elif self._match_keyword('ASC'):
                self._advance()
            items.append(OrderByItem(expr, desc))
            if not self._match(TokenType.COMMA):
                break
            self._advance()
        return items

    def _parse_limit(self):
        if not self._match_keyword('LIMIT'):
            return None
        self._advance()
        return self._parse_expr()

    def _parse_offset(self):
        if not self._match_keyword('OFFSET'):
            return None
        self._advance()
        return self._parse_expr()

    def _parse_expr(self, min_prec=0):
        return self._parse_or()

    def _parse_or(self):
        left = self._parse_and()
        while self._match_keyword('OR'):
            self._advance()
            right = self._parse_and()
            left = BinaryOp('OR', left, right)
        return left

    def _parse_and(self):
        left = self._parse_not()
        while self._match_keyword('AND'):
            self._advance()
            right = self._parse_not()
            left = BinaryOp('AND', left, right)
        return left

    def _parse_not(self):
        if self._match_keyword('NOT'):
            self._advance()
            return UnaryOp('NOT', self._parse_not())
        return self._parse_comparison()

    def _parse_comparison(self):
        left = self._parse_additive()
        tok = self._peek()

        if tok.ttype == TokenType.KEYWORD and tok.value == 'IS':
            self._advance()
            negated = False
            if self._match_keyword('NOT'):
                self._advance()
                negated = True
            self._expect(TokenType.NULL)
            return IsNullNode(left, negated)

        if tok.ttype == TokenType.KEYWORD and tok.value in ('NOT', 'LIKE', 'IN', 'BETWEEN'):
            negated = False
            if tok.value == 'NOT':
                self._advance()
                negated = True
                tok = self._peek()
            if tok.value == 'LIKE':
                self._advance()
                pattern = self._parse_additive()
                return LikeNode(left, pattern, negated)
            if tok.value == 'IN':
                self._advance()
                self._expect(TokenType.LPAREN)
                values = []
                if self._match_keyword('SELECT'):
                    sub = self._parse_select(subquery=True)
                    values = [SubqueryNode(sub)]
                else:
                    if not self._match(TokenType.RPAREN):
                        values.append(self._parse_expr())
                        while self._match(TokenType.COMMA):
                            self._advance()
                            values.append(self._parse_expr())
                self._expect(TokenType.RPAREN)
                return InNode(left, values, negated)
            if tok.value == 'BETWEEN':
                self._advance()
                low = self._parse_additive()
                self._expect(TokenType.KEYWORD, 'AND')
                high = self._parse_additive()
                return BetweenNode(left, low, high, negated)

        if tok.ttype == TokenType.OP and tok.value in ('=', '!=', '<>', '<', '>', '<=', '>='):
            self._advance()
            right = self._parse_additive()
            op = '!=' if tok.value == '<>' else tok.value
            return BinaryOp(op, left, right)

        return left

    def _parse_additive(self):
        left = self._parse_multiplicative()
        while self._match(TokenType.OP) and self._peek().value in ('+', '-', '||'):
            op = self._advance().value
            right = self._parse_multiplicative()
            left = BinaryOp(op, left, right)
        return left

    def _parse_multiplicative(self):
        left = self._parse_unary()
        while self._match(TokenType.OP) and self._peek().value in ('*', '/', '%'):
            op = self._advance().value
            right = self._parse_unary()
            left = BinaryOp(op, left, right)
        return left

    def _parse_unary(self):
        if self._match(TokenType.OP) and self._peek().value == '-':
            self._advance()
            return UnaryOp('-', self._parse_primary())
        return self._parse_primary()

    def _parse_primary(self):
        tok = self._peek()

        if tok.ttype == TokenType.LPAREN:
            self._advance()
            if self._match_keyword('SELECT'):
                sub = self._parse_select(subquery=True)
                self._expect(TokenType.RPAREN)
                return SubqueryNode(sub)
            expr = self._parse_expr()
            self._expect(TokenType.RPAREN)
            return expr

        if tok.ttype == TokenType.KEYWORD and tok.value == 'CASE':
            return self._parse_case()

        if tok.ttype == TokenType.KEYWORD and tok.value in (
            'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'COALESCE', 'NULLIF', 'CAST'
        ):
            return self._parse_function()

        if tok.ttype == TokenType.STAR:
            self._advance()
            return Star()

        if tok.ttype in (TokenType.INTEGER, TokenType.FLOAT):
            self._advance()
            return Literal(tok.value)

        if tok.ttype == TokenType.STRING:
            self._advance()
            return Literal(tok.value)

        if tok.ttype == TokenType.BOOL:
            self._advance()
            return Literal(tok.value)

        if tok.ttype == TokenType.NULL:
            self._advance()
            return Literal(None)

        if tok.ttype == TokenType.IDENTIFIER:
            self._advance()
            name = tok.value
            if self._match(TokenType.LPAREN):
                return self._parse_function_call(name)
            if self._match(TokenType.DOT):
                self._advance()
                if self._match(TokenType.STAR):
                    self._advance()
                    return Star(table=name)
                col = self._expect(TokenType.IDENTIFIER).value
                return Column(col, table=name)
            return Column(name)

        raise ParseError(f"Unexpected token {tok.value!r} at pos {tok.pos}")

    def _parse_function(self):
        name = self._advance().value.upper()
        return self._parse_function_call(name)

    def _parse_function_call(self, name):
        self._expect(TokenType.LPAREN)
        distinct = False
        args = []
        if self._match_keyword('DISTINCT'):
            self._advance()
            distinct = True
        if self._match(TokenType.STAR):
            self._advance()
            args = [Star()]
        elif not self._match(TokenType.RPAREN):
            args.append(self._parse_expr())
            while self._match(TokenType.COMMA):
                self._advance()
                args.append(self._parse_expr())
        self._expect(TokenType.RPAREN)
        return FunctionCall(name.upper(), args, distinct)

    def _parse_case(self):
        self._consume_keyword('CASE')
        whens = []
        while self._match_keyword('WHEN'):
            self._advance()
            cond = self._parse_expr()
            self._expect(TokenType.KEYWORD, 'THEN')
            result = self._parse_expr()
            whens.append((cond, result))
        else_expr = None
        if self._match_keyword('ELSE'):
            self._advance()
            else_expr = self._parse_expr()
        self._expect(TokenType.KEYWORD, 'END')
        return CaseNode(whens, else_expr)

    def _parse_insert(self):
        self._consume_keyword('INSERT', 'INTO')
        table = self._expect(TokenType.IDENTIFIER).value
        columns = []
        if self._match(TokenType.LPAREN):
            self._advance()
            columns.append(self._expect(TokenType.IDENTIFIER).value)
            while self._match(TokenType.COMMA):
                self._advance()
                columns.append(self._expect(TokenType.IDENTIFIER).value)
            self._expect(TokenType.RPAREN)
        self._expect(TokenType.KEYWORD, 'VALUES')
        all_values = []
        while True:
            self._expect(TokenType.LPAREN)
            row = [self._parse_expr()]
            while self._match(TokenType.COMMA):
                self._advance()
                row.append(self._parse_expr())
            self._expect(TokenType.RPAREN)
            all_values.append(row)
            if not self._match(TokenType.COMMA):
                break
            self._advance()
        return InsertNode(table, columns, all_values)

    def _parse_update(self):
        self._consume_keyword('UPDATE')
        table = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.KEYWORD, 'SET')
        assignments = []
        while True:
            col = self._expect(TokenType.IDENTIFIER).value
            self._expect(TokenType.OP, '=')
            val = self._parse_expr()
            assignments.append((col, val))
            if not self._match(TokenType.COMMA):
                break
            self._advance()
        where = self._parse_where()
        return UpdateNode(table, assignments, where)

    def _parse_delete(self):
        self._consume_keyword('DELETE', 'FROM')
        table = self._expect(TokenType.IDENTIFIER).value
        where = self._parse_where()
        return DeleteNode(table, where)

    def _parse_create(self):
        self._consume_keyword('CREATE')
        unique = False
        if self._match_keyword('UNIQUE'):
            self._advance()
            unique = True
        if self._match_keyword('TABLE'):
            self._advance()
            return self._parse_create_table()
        if self._match_keyword('INDEX'):
            self._advance()
            return self._parse_create_index(unique)
        raise ParseError("Expected TABLE or INDEX after CREATE")

    def _parse_create_table(self):
        table = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.LPAREN)
        columns = []
        constraints = []
        while True:
            tok = self._peek()
            if tok.ttype == TokenType.KEYWORD and tok.value == 'CONSTRAINT':
                self._advance()
                cname = self._expect(TokenType.IDENTIFIER).value
                constraints.append(self._parse_table_constraint(cname))
            elif tok.ttype == TokenType.KEYWORD and tok.value in ('PRIMARY', 'FOREIGN', 'UNIQUE', 'CHECK'):
                constraints.append(self._parse_table_constraint(None))
            else:
                columns.append(self._parse_column_def())
            if not self._match(TokenType.COMMA):
                break
            self._advance()
            if self._match(TokenType.RPAREN):
                break
        self._expect(TokenType.RPAREN)
        return CreateTableNode(table, columns, constraints)

    def _parse_column_def(self):
        name = self._expect(TokenType.IDENTIFIER).value
        col_type = self._advance().value.upper()
        col = {'name': name, 'type': col_type, 'primary_key': False,
               'nullable': True, 'unique': False, 'default': None}
        while self._peek().ttype == TokenType.KEYWORD and self._peek().value in (
            'PRIMARY', 'NOT', 'NULL', 'UNIQUE', 'DEFAULT', 'REFERENCES', 'CHECK'
        ):
            kw = self._advance().value
            if kw == 'PRIMARY':
                self._expect(TokenType.KEYWORD, 'KEY')
                col['primary_key'] = True
            elif kw == 'NOT':
                self._expect(TokenType.NULL)
                col['nullable'] = False
            elif kw == 'UNIQUE':
                col['unique'] = True
            elif kw == 'DEFAULT':
                col['default'] = self._parse_primary()
            elif kw == 'REFERENCES':
                ref_table = self._expect(TokenType.IDENTIFIER).value
                ref_col = None
                if self._match(TokenType.LPAREN):
                    self._advance()
                    ref_col = self._expect(TokenType.IDENTIFIER).value
                    self._expect(TokenType.RPAREN)
                col['references'] = (ref_table, ref_col)
        return col

    def _parse_table_constraint(self, name):
        tok = self._peek()
        kw = tok.value
        if kw == 'PRIMARY':
            self._advance()
            self._expect(TokenType.KEYWORD, 'KEY')
            self._expect(TokenType.LPAREN)
            cols = [self._expect(TokenType.IDENTIFIER).value]
            while self._match(TokenType.COMMA):
                self._advance()
                cols.append(self._expect(TokenType.IDENTIFIER).value)
            self._expect(TokenType.RPAREN)
            return {'type': 'PRIMARY KEY', 'columns': cols, 'name': name}
        if kw == 'UNIQUE':
            self._advance()
            self._expect(TokenType.LPAREN)
            cols = [self._expect(TokenType.IDENTIFIER).value]
            while self._match(TokenType.COMMA):
                self._advance()
                cols.append(self._expect(TokenType.IDENTIFIER).value)
            self._expect(TokenType.RPAREN)
            return {'type': 'UNIQUE', 'columns': cols, 'name': name}
        if kw == 'FOREIGN':
            self._advance()
            self._expect(TokenType.KEYWORD, 'KEY')
            self._expect(TokenType.LPAREN)
            col = self._expect(TokenType.IDENTIFIER).value
            self._expect(TokenType.RPAREN)
            self._expect(TokenType.KEYWORD, 'REFERENCES')
            ref_table = self._expect(TokenType.IDENTIFIER).value
            self._expect(TokenType.LPAREN)
            ref_col = self._expect(TokenType.IDENTIFIER).value
            self._expect(TokenType.RPAREN)
            return {'type': 'FOREIGN KEY', 'column': col,
                    'ref_table': ref_table, 'ref_col': ref_col, 'name': name}
        if kw == 'CHECK':
            self._advance()
            self._expect(TokenType.LPAREN)
            expr = self._parse_expr()
            self._expect(TokenType.RPAREN)
            return {'type': 'CHECK', 'expr': expr, 'name': name}
        raise ParseError(f"Unknown constraint keyword '{kw}'")

    def _parse_create_index(self, unique):
        name = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.KEYWORD, 'ON')
        table = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.LPAREN)
        column = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.RPAREN)
        return CreateIndexNode(name, table, column, unique)

    def _parse_drop(self):
        self._consume_keyword('DROP')
        if self._match_keyword('TABLE'):
            self._advance()
            table = self._expect(TokenType.IDENTIFIER).value
            return DropTableNode(table)
        if self._match_keyword('INDEX'):
            self._advance()
            name = self._expect(TokenType.IDENTIFIER).value
            table = None
            if self._match_keyword('ON'):
                self._advance()
                table = self._expect(TokenType.IDENTIFIER).value
            return DropIndexNode(name, table)
        raise ParseError("Expected TABLE or INDEX after DROP")

    def _parse_alter(self):
        self._consume_keyword('ALTER', 'TABLE')
        table = self._expect(TokenType.IDENTIFIER).value
        kw = self._advance().value
        if kw == 'ADD':
            if self._match_keyword('COLUMN'):
                self._advance()
            col = self._parse_column_def()
            return AlterTableNode(table, 'ADD COLUMN', col)
        if kw == 'DROP':
            if self._match_keyword('COLUMN'):
                self._advance()
            col = self._expect(TokenType.IDENTIFIER).value
            return AlterTableNode(table, 'DROP COLUMN', {'col_name': col})
        if kw == 'RENAME':
            if self._match_keyword('TO'):
                self._advance()
                new_name = self._expect(TokenType.IDENTIFIER).value
                return AlterTableNode(table, 'RENAME TO', {'new_name': new_name})
            if self._match_keyword('COLUMN'):
                self._advance()
            old = self._expect(TokenType.IDENTIFIER).value
            self._expect(TokenType.KEYWORD, 'TO')
            new = self._expect(TokenType.IDENTIFIER).value
            return AlterTableNode(table, 'RENAME COLUMN', {'old_name': old, 'new_name': new})
        if kw == 'MODIFY':
            if self._match_keyword('COLUMN'):
                self._advance()
            col = self._parse_column_def()
            return AlterTableNode(table, 'MODIFY COLUMN', col)
        raise ParseError(f"Unknown ALTER TABLE operation '{kw}'")

    def _parse_rollback(self):
        self._consume_keyword('ROLLBACK')
        sp = None
        if self._match_keyword('TO'):
            self._advance()
            if self._match_keyword('SAVEPOINT'):
                self._advance()
            sp = self._expect(TokenType.IDENTIFIER).value
        return RollbackNode(sp)

    def _parse_savepoint(self):
        self._consume_keyword('SAVEPOINT')
        name = self._expect(TokenType.IDENTIFIER).value
        return SavepointNode(name)

    def _parse_explain(self):
        self._consume_keyword('EXPLAIN')
        inner = self._parse_statement()
        return ExplainNode(inner)

    def _parse_truncate(self):
        self._consume_keyword('TRUNCATE')
        if self._match_keyword('TABLE'):
            self._advance()
        table = self._expect(TokenType.IDENTIFIER).value
        return TruncateNode(table)


def parse(source):
    tokens = tokenize(source)
    return Parser(tokens).parse()