import sqlite3 as _sqlite3
import os as _os
import json as _json

_connections = {}
_connection_counter = 0


def _get_conn(conn_id):
    if conn_id not in _connections:
        raise ValueError(f"Invalid or closed connection ID: {conn_id}")
    return _connections[conn_id]


def _make_entry(db_type, conn, cursor):
    return {
        "type":   db_type,
        "conn":   conn,
        "cursor": cursor,
        "ai": {
            "enabled":    False,
            "confidence": 0.80,
            "cache":      False,
            "_cache_store": {}
        }
    }


def connectSqlite(db_path):
    global _connection_counter
    conn   = _sqlite3.connect(db_path)
    cursor = conn.cursor()
    _connection_counter += 1
    conn_id = f"sqlite_{_connection_counter}"
    _connections[conn_id] = _make_entry("sqlite", conn, cursor)
    return conn_id


def connectMysql(host, user, password, database, port=3306):
    global _connection_counter
    try:
        import pymysql as _pymysql
    except ImportError:
        raise ImportError("Run: vynpkg install pymysql")
    conn   = _pymysql.connect(host=host, user=user, password=password,
                               database=database, port=int(port))
    cursor = conn.cursor()
    _connection_counter += 1
    conn_id = f"mysql_{_connection_counter}"
    _connections[conn_id] = _make_entry("mysql", conn, cursor)
    return conn_id


def connectPostgres(host, user, password, database, port=5432):
    global _connection_counter
    try:
        import psycopg2 as _psycopg2
        conn   = _psycopg2.connect(host=host, user=user, password=password,
                                    database=database, port=int(port))
        cursor = conn.cursor()
        db_type = "postgres"
    except ImportError:
        try:
            import pg8000 as _pg8000
            conn   = _pg8000.connect(host=host, user=user, password=password,
                                      database=database, port=int(port))
            cursor = conn.cursor()
            db_type = "postgres_pg8000"
        except ImportError:
            raise ImportError("Run: vynpkg install psycopg2-binary")
    _connection_counter += 1
    conn_id = f"postgres_{_connection_counter}"
    _connections[conn_id] = _make_entry(db_type, conn, cursor)
    return conn_id


def ai_enable(conn_id, confidence=0.80, cache=False):
    db = _get_conn(conn_id)
    db["ai"]["enabled"]    = True
    db["ai"]["confidence"] = confidence
    db["ai"]["cache"]      = cache


def ai_disable(conn_id):
    _get_conn(conn_id)["ai"]["enabled"] = False


def _fetch_rows(conn_id, sql, params=None):
    db     = _get_conn(conn_id)
    cursor = db["cursor"]
    cursor.execute(sql, params or [])
    cols = [c[0] for c in cursor.description] if cursor.description else []
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def query(conn_id, sql_query, params=None):
    return _fetch_rows(conn_id, sql_query, params)


def execute(conn_id, sql_query, params=None):
    db     = _get_conn(conn_id)
    conn   = db["conn"]
    cursor = db["cursor"]
    cursor.execute(sql_query, params or [])
    conn.commit()
    return cursor.lastrowid if db["type"] == "sqlite" else cursor.rowcount


def close(conn_id):
    if conn_id in _connections:
        db = _connections.pop(conn_id)
        db["cursor"].close()
        db["conn"].close()
        return True
    return False


def db_query(conn_id, sql_query, ai_prompt=None, params=None):
    from db.ai_client import ai_query as _ai_query
    rows = _fetch_rows(conn_id, sql_query, params)
    db   = _get_conn(conn_id)
    if ai_prompt and db["ai"]["enabled"]:
        cache_key = f"{sql_query}::{ai_prompt}"
        if db["ai"]["cache"] and cache_key in db["ai"]["_cache_store"]:
            return db["ai"]["_cache_store"][cache_key]
        result = _ai_query(rows, ai_prompt, db["ai"]["confidence"])
        if db["ai"]["cache"]:
            db["ai"]["_cache_store"][cache_key] = result
        return result
    return rows


def db_query_ai_table(conn_id, ai_prompt):
    from db.ai_client import ai_table_prompt as _ai_table
    db = _get_conn(conn_id)
    cursor = db["cursor"]
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'") \
        if db["type"] == "sqlite" else None
    schema = {}
    if db["type"] == "sqlite":
        tables = [r[0] for r in cursor.fetchall()]
        for t in tables:
            cursor.execute(f"PRAGMA table_info({t})")
            schema[t] = [r[1] for r in cursor.fetchall()]
    sql = _ai_table(ai_prompt, schema)
    return _fetch_rows(conn_id, sql)


def ai_filter(conn_id_or_rows, prompt, confidence=0.80):
    from db.ai_client import ai_filter as _ai_filter
    if isinstance(conn_id_or_rows, list):
        return _ai_filter(conn_id_or_rows, prompt, confidence)
    db   = _get_conn(conn_id_or_rows)
    conf = db["ai"]["confidence"] if db["ai"]["enabled"] else confidence
    return _ai_filter([], prompt, conf)


def ai_rank(rows, prompt, confidence=0.80):
    from db.ai_client import ai_rank as _ai_rank
    return _ai_rank(rows, prompt, confidence)


def ai_column(rows, col_prompt, col_name="ai_col"):
    from db.ai_client import ai_column as _ai_column
    return _ai_column(rows, col_prompt, col_name)


def ai_pipe(rows, *prompts):
    from db.ai_client import ai_query as _ai_query
    result = rows
    for prompt in prompts:
        result = _ai_query(result, prompt)
    return result


def ai_summarize(conn_id_or_rows, prompt=None):
    from db.ai_client import ai_summarize as _ai_summarize
    if isinstance(conn_id_or_rows, list):
        return _ai_summarize(conn_id_or_rows, prompt)
    rows = list(_connections.get(conn_id_or_rows, {}).get("_last_rows", []))
    return _ai_summarize(rows, prompt)


def ai_spreadsheet(conn_id_or_rows, prompt=None):
    from db.ai_client import ai_spreadsheet as _ai_spreadsheet
    if isinstance(conn_id_or_rows, list):
        return _ai_spreadsheet(conn_id_or_rows, prompt)
    rows = list(_connections.get(conn_id_or_rows, {}).get("_last_rows", []))
    return _ai_spreadsheet(rows, prompt)