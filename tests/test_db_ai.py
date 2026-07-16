import os
import sys
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)

from db import ai_client
from db import db


class DatabaseAITests(unittest.TestCase):
    def test_ai_query_parses_json_array_response(self):
        rows = [{"name": "Ada"}, {"name": "Grace"}]
        with mock.patch("db.ai_client._call_space", return_value='[{"name": "Ada"}]'):
            self.assertEqual(
                ai_client.ai_query(rows, "only Ada"),
                [{"name": "Ada"}],
            )

    def test_ai_table_prompt_alias_generates_sql(self):
        with mock.patch("db.ai_client._call_space", return_value="SELECT name FROM users"):
            self.assertEqual(
                ai_client.ai_table_prompt("show users", {"users": ["name"]}),
                "SELECT name FROM users",
            )

    def test_db_query_ai_table_uses_generated_sql(self):
        conn = db.connectSqlite(":memory:")
        try:
            db.execute(conn, "CREATE TABLE users (name TEXT)")
            db.execute(conn, "INSERT INTO users (name) VALUES ('Ada')")
            with mock.patch("db.ai_client._call_space", return_value="SELECT name FROM users"):
                self.assertEqual(
                    db.db_query_ai_table(conn, "show users"),
                    [{"name": "Ada"}],
                )
        finally:
            db.close(conn)


if __name__ == "__main__":
    unittest.main()
