import re

DB_QUERY_RE     = re.compile(r'^DB_QUERY\s+(?P<conn>\w+)\s+(?P<sql>"[^"]*"|\'[^\']*\'|"""[\s\S]*?""")\s*(?:AS\s+(?P<var>\w+))?$', re.MULTILINE)
DB_QUERY_ML_RE  = re.compile(r'^DB_QUERY\s+(?P<conn>\w+)\s*$')
AI_INLINE_RE    = re.compile(r'AI\s*\(\s*"(?P<prompt>[^"]+)"\s*\)')
AI_LINE_RE      = re.compile(r'^AI\s+"(?P<prompt>[^"]+)"\s*$')
AS_RE           = re.compile(r'^AS\s+(?P<var>\w+)\s*$')
PIPE_AI_RE      = re.compile(r'^\|>\s*AI\s*\("(?P<prompt>[^"]+)"\)\s*$')
AI_FILTER_RE    = re.compile(r'^(?P<var>\w+)\s*=\s*AI\.Filter\s*\(\s*(?P<rows>\w+)\s*,\s*"(?P<prompt>[^"]+)"\s*\)$')
AI_RANK_RE      = re.compile(r'^(?P<var>\w+)\s*=\s*AI\.Rank\s*\(\s*(?P<rows>\w+)\s*,\s*"(?P<prompt>[^"]+)"\s*\)$')
AI_SUMMARIZE_RE = re.compile(r'^(?P<var>\w+)\s*=\s*AI\.Summarize\s*\(\s*(?P<rows>\w+)\s*(?:,\s*"(?P<prompt>[^"]+)")?\s*\)$')
AI_SHEET_RE     = re.compile(r'^(?P<var>\w+)\s*=\s*AI\.Spreadsheet\s*\(\s*(?P<rows>\w+)\s*(?:,\s*"(?P<prompt>[^"]+)")?\s*\)$')
CONNECT_RE      = re.compile(r'^(?P<var>\w+)\s*=\s*connect\s*\(\s*(?P<dbtype>sqlite|postgres|mysql)\s*,\s*(?P<args>.+)\s*\)$')
AI_ENABLE_RE    = re.compile(r'^AI\.enable\s*\(\s*(?P<conn>\w+)(?:\s*,\s*confidence\s*=\s*(?P<conf>[\d.]+))?\s*\)$')
AI_DISABLE_RE   = re.compile(r'^AI\.disable\s*\(\s*(?P<conn>\w+)\s*\)$')
CLOSE_RE        = re.compile(r'^db\.close\s*\(\s*(?P<conn>\w+)\s*\)$')


def _strip_quotes(s):
    s = s.strip()
    if s.startswith('"""') and s.endswith('"""'):
        return s[3:-3].strip()
    if (s.startswith('"') and s.endswith('"')) or \
       (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s


def _parse_connect_args(dbtype, args_str):
    args = [a.strip().strip('"\'') for a in args_str.split(',')]
    if dbtype == 'sqlite':
        return {'db_path': args[0]}
    elif dbtype == 'mysql':
        keys = ['host', 'user', 'password', 'database', 'port']
        return dict(zip(keys, args))
    elif dbtype == 'postgres':
        kv = {}
        for part in args_str.split(','):
            part = part.strip()
            if '=' in part:
                k, v = part.split('=', 1)
                kv[k.strip()] = v.strip().strip('"\'')
            else:
                kv['dsn'] = part.strip().strip('"\'')
        return kv


def _extract_ai_prompt(sql):
    m = AI_INLINE_RE.search(sql)
    if m:
        clean_sql = AI_INLINE_RE.sub('', sql).strip()
        clean_sql = re.sub(r',\s*,', ',', clean_sql)
        clean_sql = re.sub(r',\s*FROM', ' FROM', clean_sql)
        return clean_sql, m.group('prompt')
    m = re.search(r'^\s*AI\s+"([^"]+)"\s*$', sql, re.MULTILINE)
    if m:
        clean_sql = re.sub(r'^\s*AI\s+"[^"]+"\s*$', '', sql, flags=re.MULTILINE).strip()
        return clean_sql, m.group(1)
    m = re.search(r'FROM\s+AI\s*\(\s*"([^"]+)"\s*\)', sql, re.IGNORECASE)
    if m:
        return None, m.group(1)
    return sql, None


def handle_connect(line, variables, eval_expression):
    m = CONNECT_RE.match(line.strip())
    if not m:
        return False
    import db.db as _db
    var    = m.group('var')
    dbtype = m.group('dbtype')
    args   = _parse_connect_args(dbtype, m.group('args'))
    if dbtype == 'sqlite':
        variables[var] = _db.connectSqlite(args['db_path'])
    elif dbtype == 'mysql':
        variables[var] = _db.connectMysql(
            args.get('host','localhost'),
            args.get('user',''),
            args.get('password',''),
            args.get('database',''),
            args.get('port', 3306)
        )
    elif dbtype == 'postgres':
        if 'dsn' in args:
            parts = {}
            for tok in args['dsn'].split():
                if '=' in tok:
                    k, v = tok.split('=', 1)
                    parts[k] = v
            variables[var] = _db.connectPostgres(
                parts.get('host','localhost'),
                parts.get('user',''),
                parts.get('password',''),
                parts.get('dbname', parts.get('database','')),
                int(parts.get('port', 5432))
            )
        else:
            variables[var] = _db.connectPostgres(
                args.get('host','localhost'),
                args.get('user',''),
                args.get('password',''),
                args.get('database',''),
                int(args.get('port', 5432))
            )
    return True


def handle_ai_enable(line, variables):
    m = AI_ENABLE_RE.match(line.strip())
    if not m:
        return False
    import db.db as _db
    conn_id = variables.get(m.group('conn'), m.group('conn'))
    conf    = float(m.group('conf')) if m.group('conf') else 0.80
    _db.ai_enable(conn_id, confidence=conf)
    return True


def handle_ai_disable(line, variables):
    m = AI_DISABLE_RE.match(line.strip())
    if not m:
        return False
    import db.db as _db
    conn_id = variables.get(m.group('conn'), m.group('conn'))
    _db.ai_disable(conn_id)
    return True


def handle_close(line, variables):
    m = CLOSE_RE.match(line.strip())
    if not m:
        return False
    import db.db as _db
    conn_id = variables.get(m.group('conn'), m.group('conn'))
    _db.close(conn_id)
    return True


def handle_db_query(line, variables, readline, eval_expression, execute_line):
    import db.db as _db

    # Syntax 3: pipe chain
    # users = DB_QUERY conn "sql" |> AI("...") |> AI("...") AS result
    pipe_line = line.strip()
    pipe_match = re.match(
        r'^(?:(?P<assign>\w+)\s*=\s*)?DB_QUERY\s+(?P<conn>\w+)\s+"(?P<sql>[^"]+)"\s*(?P<pipes>(?:\|>\s*AI\s*\("[^"]+"\)\s*)+)AS\s+(?P<var>\w+)$',
        pipe_line
    )
    if pipe_match:
        conn_id  = variables.get(pipe_match.group('conn'), pipe_match.group('conn'))
        sql      = pipe_match.group('sql')
        var      = pipe_match.group('var')
        pipes_str= pipe_match.group('pipes')
        prompts  = re.findall(r'AI\s*\("([^"]+)"\)', pipes_str)
        rows     = _db.query(conn_id, sql)
        for prompt in prompts:
            rows = _db.ai_pipe(rows, prompt)
        variables[var] = rows
        return True

    # Syntax 1: DB_QUERY conn "sql"\n AI "prompt"\n AS result
    m1 = re.match(r'^DB_QUERY\s+(?P<conn>\w+)\s+"(?P<sql>[^"]+)"$', line.strip())
    if m1:
        conn_id    = variables.get(m1.group('conn'), m1.group('conn'))
        sql        = m1.group('sql')
        ai_prompt  = None
        var        = None
        next1 = readline()
        if next1 and AI_LINE_RE.match(next1.strip()):
            ai_prompt = AI_LINE_RE.match(next1.strip()).group('prompt')
            next2 = readline()
            if next2 and AS_RE.match(next2.strip()):
                var = AS_RE.match(next2.strip()).group('var')
        elif next1 and AS_RE.match(next1.strip()):
            var = AS_RE.match(next1.strip()).group('var')
        rows = _db.db_query(conn_id, sql, ai_prompt)
        if var:
            variables[var] = rows
        return True

    # Syntax 2: multiline DB_QUERY with triple-quoted SQL
    m2 = DB_QUERY_ML_RE.match(line.strip())
    if m2:
        conn_id = variables.get(m2.group('conn'), m2.group('conn'))
        sql_lines = []
        while True:
            l = readline()
            if not l:
                continue
            if l.strip() == '"""':
                break
            sql_lines.append(l)
        full_sql = '\n'.join(sql_lines)
        var      = None
        next_l   = readline()
        if next_l and AS_RE.match(next_l.strip()):
            var = AS_RE.match(next_l.strip()).group('var')
        clean_sql, ai_prompt = _extract_ai_prompt(full_sql)
        if clean_sql is None:
            rows = _db.db_query_ai_table(conn_id, ai_prompt)
        else:
            rows = _db.db_query(conn_id, clean_sql, ai_prompt)
        if var:
            variables[var] = rows
        return True

    return False


def handle_ai_method(line, variables):
    import db.db as _db

    # Syntax 4a: var = AI.Filter(rows, "prompt")
    m = AI_FILTER_RE.match(line.strip())
    if m:
        rows   = variables.get(m.group('rows'), [])
        result = _db.ai_filter(rows, m.group('prompt'))
        variables[m.group('var')] = result
        return True

    # Syntax 4b: var = AI.Rank(rows, "prompt")
    m = AI_RANK_RE.match(line.strip())
    if m:
        rows   = variables.get(m.group('rows'), [])
        result = _db.ai_rank(rows, m.group('prompt'))
        variables[m.group('var')] = result
        return True

    # Syntax 4c: var = AI.Summarize(rows)
    m = AI_SUMMARIZE_RE.match(line.strip())
    if m:
        rows   = variables.get(m.group('rows'), [])
        prompt = m.group('prompt')
        result = _db.ai_summarize(rows, prompt)
        variables[m.group('var')] = result
        return True

    # Syntax 4d: var = AI.Spreadsheet(rows)
    m = AI_SHEET_RE.match(line.strip())
    if m:
        rows   = variables.get(m.group('rows'), [])
        prompt = m.group('prompt')
        result = _db.ai_spreadsheet(rows, prompt)
        variables[m.group('var')] = result
        return True

    return False


def register_db_functions(variables):
    import db.db as _db
    variables['connect']        = _connect_dispatch
    variables['db']             = _DbNamespace()
    variables['AI']             = _AiNamespace()
    variables['db_query']       = _db.db_query
    variables['db_execute']     = _db.execute
    variables['db_close']       = _db.close


def _connect_dispatch(dbtype, *args, **kwargs):
    import db.db as _db
    t = str(dbtype).lower()
    if t == 'sqlite':
        return _db.connectSqlite(args[0] if args else kwargs.get('db_path'))
    elif t == 'mysql':
        return _db.connectMysql(*args, **kwargs)
    elif t in ('postgres', 'postgresql'):
        return _db.connectPostgres(*args, **kwargs)
    raise ValueError(f"Unknown db type: {dbtype}")


class _DbNamespace:
    def close(self, conn_id):
        import db.db as _db
        return _db.close(conn_id)
    def query(self, conn_id, sql, params=None):
        import db.db as _db
        return _db.query(conn_id, sql, params)
    def execute(self, conn_id, sql, params=None):
        import db.db as _db
        return _db.execute(conn_id, sql, params)


class _AiNamespace:
    def Filter(self, rows, prompt, confidence=0.80):
        import db.db as _db
        return _db.ai_filter(rows, prompt, confidence)
    def Rank(self, rows, prompt, confidence=0.80):
        import db.db as _db
        return _db.ai_rank(rows, prompt, confidence)
    def Summarize(self, rows, prompt=None):
        import db.db as _db
        return _db.ai_summarize(rows, prompt)
    def Spreadsheet(self, rows, prompt=None):
        import db.db as _db
        return _db.ai_spreadsheet(rows, prompt)
    def enable(self, conn_id, confidence=0.80):
        import db.db as _db
        _db.ai_enable(conn_id, confidence)
    def disable(self, conn_id):
        import db.db as _db
        _db.ai_disable(conn_id)