import json
import urllib.request
import urllib.parse
import urllib.error

SPACE_URL = "https://istiger2011-jarvis-space.hf.space"
_session_hash = None


def _hf_predict(prompt, context_json):
    global _session_hash
    import random
    import string
    if _session_hash is None:
        _session_hash = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

    payload = json.dumps({
        "data": [prompt, context_json],
        "session_hash": _session_hash
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{SPACE_URL}/run/predict",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            data = result.get("data", [])
            return data[0] if data else ""
    except urllib.error.URLError as exc:
        raise RuntimeError(f"AI Space unreachable: {exc}")
    except Exception as exc:
        raise RuntimeError(f"AI request failed: {exc}")


def ai_query(rows, prompt, confidence=0.80):
    context = json.dumps(rows[:200])
    raw = _hf_predict(prompt, context)
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
        return [{"ai_response": raw}]
    return [{"ai_response": str(raw)}]


def ai_filter(rows, prompt, confidence=0.80):
    context = json.dumps(rows[:200])
    filter_prompt = f"Filter these rows and return only matching ones as JSON array. Criteria: {prompt}"
    raw = _hf_predict(filter_prompt, context)
    if isinstance(raw, list):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return rows


def ai_column(rows, col_prompt, col_name):
    results = []
    for row in rows:
        single_prompt = f"For this row: {json.dumps(row)}\nCompute: {col_prompt}\nReturn just the value."
        raw = _hf_predict(single_prompt, "{}")
        new_row = dict(row)
        new_row[col_name] = raw.strip() if isinstance(raw, str) else raw
        results.append(new_row)
    return results


def ai_rank(rows, prompt, confidence=0.80):
    context = json.dumps(rows[:200])
    rank_prompt = f"Rank these rows from most to least relevant. Criteria: {prompt}. Return as JSON array in ranked order."
    raw = _hf_predict(rank_prompt, context)
    try:
        return json.loads(raw)
    except Exception:
        return rows


def ai_table_prompt(prompt, schema_info):
    full_prompt = (
        f"Given this database schema: {json.dumps(schema_info)}\n"
        f"Generate a SQL SELECT query for: {prompt}\n"
        f"Return only the SQL query, nothing else."
    )
    raw = _hf_predict(full_prompt, "{}")
    return raw.strip() if isinstance(raw, str) else str(raw)


def ai_summarize(rows, prompt=None):
    context = json.dumps(rows[:200])
    p = prompt or "Summarize this data in plain English."
    raw = _hf_predict(p, context)
    return raw.strip() if isinstance(raw, str) else str(raw)


def ai_spreadsheet(rows, prompt=None):
    context = json.dumps(rows[:200])
    p = prompt or "Convert this data into a clean spreadsheet format with headers."
    raw = _hf_predict(p, context)
    return raw.strip() if isinstance(raw, str) else str(raw)