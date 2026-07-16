import json
import urllib.request
import urllib.error

SPACE_URL  = "https://istiger2011-jarvis-space.hf.space"
PREDICT_URL = f"{SPACE_URL}/run/predict"

# From your space HTML: it has a Radio + Textbox input
# Radio selects the mode, Textbox is the prompt/context
# Adjust RADIO_CHOICE if your space uses different labels
RADIO_CHOICE = "New entry"   # visible in your space HTML


def _call_space(prompt_text, timeout=30):
    """
    POST to your Gradio space /run/predict endpoint.
    Your space takes: [radio_choice, textbox_text]
    Returns the first data item from the response.
    """
    payload = json.dumps({
        "data": [RADIO_CHOICE, prompt_text]
    }).encode("utf-8")

    req = urllib.request.Request(
        PREDICT_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
            data = raw.get("data", [])
            return data[0] if data else ""
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"Space returned HTTP {exc.code}: {exc.reason}. "
            f"Check that your space is running at {SPACE_URL}"
        )
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Cannot reach space at {SPACE_URL}: {exc.reason}. "
            f"Is the space awake?"
        )
    except Exception as exc:
        raise RuntimeError(f"AI call failed: {exc}")


def _build_prompt(instruction, context_rows):
    """
    Combine a user instruction with row context into one
    prompt string since your space takes a single Textbox.
    """
    if not context_rows:
        return instruction
    sample = context_rows[:100]
    ctx = json.dumps(sample, default=str, ensure_ascii=False)
    return (
        f"{instruction}\n\n"
        f"Here is the data (JSON):\n{ctx}\n\n"
        f"Respond only with a valid JSON array of objects."
    )


def _parse_response(raw):
    """
    Try to parse the model response as a list of dicts.
    Falls back to wrapping in an ai_response field.
    """
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return [raw]
    if isinstance(raw, str):
        s = raw.strip()
        # Strip markdown code fences if present
        if s.startswith("```"):
            lines = s.splitlines()
            s = "\n".join(
                l for l in lines
                if not l.startswith("```")
            ).strip()
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                return [parsed]
        except json.JSONDecodeError:
            pass
        return [{"ai_response": s}]
    return [{"ai_response": str(raw)}]


def ai_query(rows, prompt, confidence=0.80):
    """
    Send rows + prompt to the space.
    Returns a list of dicts — either filtered/processed rows
    or the AI's structured response.
    """
    full_prompt = _build_prompt(prompt, rows)
    raw = _call_space(full_prompt)
    return _parse_response(raw)


def ai_filter(rows, prompt, confidence=0.80):
    """
    Ask the model to return only the matching rows.
    """
    instruction = (
        f"Filter the data below and return ONLY the rows "
        f"that match this criteria: {prompt}\n"
        f"Return a valid JSON array of the matching rows only."
    )
    full_prompt = _build_prompt(instruction, rows)
    raw = _call_space(full_prompt)
    result = _parse_response(raw)
    # If model returned non-list fallback, return original rows
    if result and "ai_response" in result[0]:
        return rows
    return result


def ai_rank(rows, prompt, confidence=0.80):
    """
    Ask the model to rank rows by relevance and return them sorted.
    """
    instruction = (
        f"Rank the following rows from MOST to LEAST relevant "
        f"based on: {prompt}\n"
        f"Return a valid JSON array in ranked order."
    )
    full_prompt = _build_prompt(instruction, rows)
    raw = _call_space(full_prompt)
    result = _parse_response(raw)
    if result and "ai_response" in result[0]:
        return rows
    return result


def ai_column(rows, col_prompt, col_name="ai_col"):
    """
    For each row, ask the model to compute a derived value.
    Adds that value as a new column on each row.
    """
    results = []
    for row in rows:
        instruction = (
            f"For this single data row: {json.dumps(row, default=str)}\n"
            f"Compute the following and return ONLY the value "
            f"(no explanation, no JSON wrapper): {col_prompt}"
        )
        raw = _call_space(instruction)
        new_row = dict(row)
        if isinstance(raw, str):
            new_row[col_name] = raw.strip()
        else:
            new_row[col_name] = raw
        results.append(new_row)
    return results


def ai_pipe(rows, *prompts):
    """
    Chain multiple AI prompts — output of each becomes input of next.
    """
    result = rows
    for prompt in prompts:
        result = ai_query(result, prompt)
    return result


def ai_summarize(rows, prompt=None):
    """
    Ask the model for a plain-English summary of the data.
    Returns a string.
    """
    instruction = prompt or "Summarize this data in clear plain English."
    full_prompt = _build_prompt(instruction, rows)
    raw = _call_space(full_prompt)
    if isinstance(raw, str):
        return raw.strip()
    return str(raw)


def ai_spreadsheet(rows, prompt=None):
    """
    Ask the model to format data as a spreadsheet/CSV.
    Returns a string.
    """
    instruction = (
        prompt or
        "Convert this data into a clean CSV spreadsheet format "
        "with a header row. Use comma as delimiter."
    )
    full_prompt = _build_prompt(instruction, rows)
    raw = _call_space(full_prompt)
    if isinstance(raw, str):
        return raw.strip()
    return str(raw)


def ai_sql(prompt, schema_info):
    """
    Ask the model to generate a SQL query from a natural language prompt.
    Returns the SQL string.
    """
    schema_str = json.dumps(schema_info, default=str)
    instruction = (
        f"Given this database schema:\n{schema_str}\n\n"
        f"Write a SQL SELECT query that answers: {prompt}\n"
        f"Return ONLY the SQL query, nothing else."
    )
    raw = _call_space(instruction)
    if isinstance(raw, str):
        sql = raw.strip()
        if sql.startswith("```"):
            lines = sql.splitlines()
            sql = "\n".join(
                l for l in lines
                if not l.startswith("```")
            ).strip()
        return sql
    return str(raw)


def ai_table_prompt(prompt, schema_info):
    return ai_sql(prompt, schema_info)


def wake_space():
    """
    Ping the space to wake it up if it went to sleep.
    Returns True if reachable.
    """
    try:
        req = urllib.request.Request(
            SPACE_URL, method="GET"
        )
        with urllib.request.urlopen(req, timeout=10):
            return True
    except Exception:
        return False
