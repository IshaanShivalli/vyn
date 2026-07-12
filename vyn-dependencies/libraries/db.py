"""
db.vyn implementation.
Provides a unified interface for SQLite3, MySQL, and PostgreSQL.
"""
import sqlite3 as _sqlite3
import os as _os

# Registry of active database connections
_connections = {}
_connection_counter = 0

def _get_conn(conn_id):
    if conn_id not in _connections:
        raise ValueError(f"Invalid or closed connection ID: {conn_id}")
    return _connections[conn_id]

def connectSqlite(db_path):
    """Connect to a SQLite3 database."""
    global _connection_counter
    conn = _sqlite3.connect(db_path)
    _connection_counter += 1
    conn_id = f"sqlite_{_connection_counter}"
    _connections[conn_id] = {
        "type": "sqlite",
        "conn": conn,
        "cursor": conn.cursor(),

        # AI Configuration
        "ai": {
            "enabled": False,
            "provider": None,
            "model": None,
            "cache": False,
            "confidence": 0.80
        }
    }
    return conn_id

def connectMysql(host, user, password, database, port=3306):
    """Connect to a MySQL database."""
    global _connection_counter
    try:
        import pymysql as _pymysql
    except ImportError:
        raise ImportError("MySQL driver not installed. Please run: pip install pymysql")
    
    conn = _pymysql.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=int(port)
    )
    _connection_counter += 1
    conn_id = f"mysql_{_connection_counter}"
    _connections[conn_id] = {
        "type": "mysql",
        "conn": conn,
        "cursor": conn.cursor(),
        "ai": {
            "enabled": False,
            "provider": None,
            "model": None,
            "cache": False,
            "confidence": 0.80
        }
    }
    return conn_id

def connectPostgres(host, user, password, database, port=5432):
    """Connect to a PostgreSQL database."""
    global _connection_counter
    try:
        import psycopg2 as _psycopg2
    except ImportError:
        try:
            import pg8000 as _pg8000
            # pg8000 interface
            conn = _pg8000.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                port=int(port)
            )
            _connection_counter += 1
            conn_id = f"postgres_{_connection_counter}"
            _connections[conn_id] = {
                "type": "postgres_pg8000",
                "conn": conn,
                "cursor": conn.cursor(),
                "ai": {
                    "enabled": False,
                    "provider": None,
                    "model": None,
                    "cache": False,
                    "confidence": 0.80
                }
            }
            return conn_id
        except ImportError:
            raise ImportError("PostgreSQL driver not installed. Please run: pip install psycopg2-binary or pip install pg8000")
            
    conn = _psycopg2.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        port=int(port)
    )
    _connection_counter += 1
    conn_id = f"postgres_{_connection_counter}"
    _connections[conn_id] = {
        "type": "postgres",
        "conn": conn,
        "cursor": conn.cursor()
    }
    return conn_id

def query(conn_id, sql_query, params=None):
    """Execute a query and return rows as list of dictionaries."""
    db_obj = _get_conn(conn_id)
    cursor = db_obj["cursor"]
    
    if params is None:
        params = []
    elif not isinstance(params, (list, tuple)):
        params = [params]
        
    cursor.execute(sql_query, params)
    
    # Get column names
    columns = [col[0] for col in cursor.description] if cursor.description else []
    
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
        
    return results

def execute(conn_id, sql_query, params=None):
    """Execute an insert/update/delete command. Returns affected row count or lastrowid."""
    db_obj = _get_conn(conn_id)
    conn = db_obj["conn"]
    cursor = db_obj["cursor"]
    
    if params is None:
        params = []
    elif not isinstance(params, (list, tuple)):
        params = [params]
        
    cursor.execute(sql_query, params)
    conn.commit()
    
    if db_obj["type"] == "sqlite":
        return cursor.lastrowid or cursor.rowcount
    return cursor.rowcount

def close(conn_id):
    """Close the connection."""
    if conn_id in _connections:
        db_obj = _connections.pop(conn_id)
        db_obj["cursor"].close()
        db_obj["conn"].close()
        return True
    return False
