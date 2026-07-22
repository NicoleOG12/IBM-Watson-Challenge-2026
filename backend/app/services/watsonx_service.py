"""
watsonx_service.py — IBM watsonx.ai integration for NL → SQL generation.

Flow:
    1. Build a schema-aware prompt (via schema_service) + user query
    2. Call the watsonx.ai Inference REST endpoint (or return a mock)
    3. Parse the JSON response envelope → LLMResult(sql, explanation)

Prompt engineering enforces:
    - Only SELECT statements are allowed
    - No DELETE / UPDATE / DROP / INSERT / ALTER / TRUNCATE / EXEC
    - Only analytical / read-only queries

Set WATSONX_MOCK=True in .env to bypass the API and get a deterministic
mock response — useful during local development and CI.
"""

import json
import logging
import re
from typing import Optional

import httpx

from app.config import get_settings
from app.models.llm import LLMRequest, LLMResult
from app.models.schema import SchemaContext

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Fallback prompt template (used when no schema is available)
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT_FALLBACK = """\
You are an expert SQL analyst assistant integrated into an AI-powered data copilot.
Your ONLY job is to translate a natural language question into a valid SQL SELECT query.

STRICT RULES — you MUST follow all of them:
1. Output ONLY a valid SQL SELECT statement. No other SQL verbs are permitted.
2. NEVER generate DELETE, UPDATE, INSERT, DROP, ALTER, TRUNCATE, CREATE, EXEC,
   GRANT, REVOKE, MERGE, or any other data-modification or DDL statement.
3. If the user's question implies a data change, politely explain that you can
   only run analytical (read-only) queries and set sql to an empty string.
4. Always include an explanation field that describes in plain English what
   the SQL does.
5. Return your response as valid JSON with exactly these two keys:
   {{ "sql": "<SELECT statement>", "explanation": "<plain English explanation>" }}
6. Do not include markdown code fences, comments, or any text outside the JSON object.

EXAMPLE INPUT:
  Show me total sales by region for last quarter.

EXAMPLE OUTPUT:
  {{
    "sql": "SELECT region, SUM(amount) AS total_sales FROM sales WHERE sale_date >= DATE_TRUNC('quarter', NOW() - INTERVAL '3 months') GROUP BY region ORDER BY total_sales DESC",
    "explanation": "Aggregates total sales by region for the previous quarter, ordered from highest to lowest."
  }}

Translate the following question into a SQL SELECT query following the rules above.

Question: {query}
"""


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_FORBIDDEN_PATTERN = re.compile(
    r"\b(DELETE|UPDATE|INSERT|DROP|ALTER|TRUNCATE|CREATE|EXEC|EXECUTE|"
    r"GRANT|REVOKE|MERGE|REPLACE)\b",
    re.IGNORECASE,
)


def _is_safe_sql(sql: str) -> bool:
    """Return True only if the SQL contains no forbidden verbs."""
    return not bool(_FORBIDDEN_PATTERN.search(sql))


# ---------------------------------------------------------------------------
# Mock response
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Destructive-intent detector — applied to the *natural language* question
# before SQL generation, mirroring the LLM's system-prompt rule #3.
# ---------------------------------------------------------------------------

_DESTRUCTIVE_NL_PATTERN = re.compile(
    r"\b("
    # Unambiguous DML/DDL verbs (always destructive regardless of context)
    r"delete\b|truncate\b|"
    # DROP only when a DB-object noun follows (within 4 words), so that
    # "sales drop", "price drop", "revenue drop" are not flagged.
    r"drop(?:\s+\w+){0,3}\s+(?:table|column|index|view|database|schema|procedure|trigger)\b|"
    # INSERT when targeting a data object or using "into"
    r"insert(?:\s+\w+){0,4}\s+(?:row|record|entry)s?\b|"
    r"insert\s+(?:\w+\s+)?into\b|"
    # UPDATE when targeting a specific data object
    r"update\s+(?:(?:the|a|an|my|this)\s+)?(?:table|column|row|record|price|field|value|data)\b|"
    # DDL verbs
    r"alter\s+(?:\w+\s+)?(?:table|column|database|schema)\b|"
    r"create(?:\s+\w+){0,3}\s+(?:table|column|database|schema|index|view|procedure)\b|"
    # Plain-language destructive equivalents
    r"remove\s+(?:(?:all|the|every|a|an)\s+)?(?:row|record|entry|data|user)s?\b|"
    r"erase\s+(?:(?:all|the)\s+)?(?:row|record|data|table|entry)s?\b|"
    r"wipe\s+(?:(?:the|all)\s+)?(?:database|table|data|record)s?\b|"
    r"modify\s+(?:(?:the|a|an)\s+)?(?:table|column|row|record|data|schema)\b|"
    r"overwrite\s+(?:(?:the|a)\s+)?(?:table|record|data)\b"
    r")",
    re.IGNORECASE,
)


def _is_destructive_intent(query: str) -> bool:
    """
    Return True when the natural-language query appears to request a
    data-modification or DDL operation rather than a read-only analysis.
    """
    return bool(_DESTRUCTIVE_NL_PATTERN.search(query))


# ---------------------------------------------------------------------------
# Question-aware mock responses
# Each entry is (keyword_list, sql, explanation).
# The first entry whose keywords all appear (case-insensitive) in the query wins.
# The final entry acts as the default fallback.
<<<<<<< HEAD
# All SQL is written against the real Glue/Athena schema (db_watson):
#   venda_parquet    (id_venda, id_loja, id_cliente, id_produto, qt_quantidade,
#                     vl_total_venda, dt_venda, nm_cliente, nm_filial,
#                     nm_produto, nm_categoria, vl_preco_unitario)
#   cliente_parquet  (id_identificador, nm_nome, ds_sobrenome, nu_cpf,
#                     dt_nascimento, ct_cidade, sg_estado, ...)
#   loja_parquet     (id_identificador, nm_filial, nu_cnpj, ct_cidade,
#                     sg_estado, fl_status, ...)
#   produtos_parquet (id_identificador, nm_nome, ds_descricao, nm_categoria,
#                     vl_preco_unitario, qt_estoque)
# ---------------------------------------------------------------------------

_MOCK_SCENARIOS: list[tuple[list[str], str, str]] = [
    # Top clientes por receita
    (
        ["top", "cliente", "receita"],
        """SELECT nm_cliente,
       COUNT(*) AS total_vendas,
       ROUND(SUM(vl_total_venda), 2) AS receita_total
FROM venda_parquet
GROUP BY nm_cliente
ORDER BY receita_total DESC
LIMIT 10""",
        "Lista os 10 clientes com maior receita total acumulada.",
    ),
    # Ticket médio por filial
    (
        ["ticket", "filial"],
        """SELECT nm_filial,
       COUNT(*) AS total_vendas,
       ROUND(AVG(vl_total_venda), 2) AS ticket_medio,
       ROUND(SUM(vl_total_venda), 2) AS receita_total
FROM venda_parquet
GROUP BY nm_filial
ORDER BY ticket_medio DESC""",
        "Calcula o ticket médio e a receita total por filial.",
    ),
    # Vendas por categoria
    (
        ["categoria"],
        """SELECT nm_categoria,
       COUNT(*) AS total_vendas,
       SUM(qt_quantidade) AS unidades_vendidas,
       ROUND(SUM(vl_total_venda), 2) AS receita_total
FROM venda_parquet
GROUP BY nm_categoria
ORDER BY receita_total DESC""",
        "Agrega total de vendas, unidades vendidas e receita por categoria de produto.",
    ),
    # Estoque crítico / baixo estoque
    (
        ["estoque"],
        """SELECT nm_nome,
       nm_categoria,
       vl_preco_unitario,
       qt_estoque
FROM produtos_parquet
ORDER BY qt_estoque ASC
LIMIT 20""",
        "Lista os 20 produtos com menor estoque disponível.",
    ),
    # Lojas ativas / inativas
    (
        ["loja"],
        """SELECT ct_cidade,
       sg_estado,
       COUNT(*) AS total_lojas,
       SUM(CASE WHEN fl_status THEN 1 ELSE 0 END) AS lojas_ativas,
       SUM(CASE WHEN NOT fl_status THEN 1 ELSE 0 END) AS lojas_inativas
FROM loja_parquet
GROUP BY ct_cidade, sg_estado
ORDER BY total_lojas DESC""",
        "Mostra a quantidade de lojas ativas e inativas por cidade e estado.",
    ),
    # Desempenho por produto
    (
        ["produto"],
        """SELECT nm_produto,
       nm_categoria,
       COUNT(*) AS total_vendas,
       SUM(qt_quantidade) AS unidades_vendidas,
       ROUND(SUM(vl_total_venda), 2) AS receita_total
FROM venda_parquet
GROUP BY nm_produto, nm_categoria
ORDER BY receita_total DESC""",
        "Mostra receita total e unidades vendidas por produto.",
    ),
    # Comparativo Q2 vs Q3
    (
        ["q2", "q3"],
        """SELECT nm_produto,
       ROUND(SUM(CASE WHEN SUBSTR(dt_venda,6,2) IN ('04','05','06') THEN vl_total_venda ELSE 0 END), 2) AS receita_q2,
       ROUND(SUM(CASE WHEN SUBSTR(dt_venda,6,2) IN ('07','08','09') THEN vl_total_venda ELSE 0 END), 2) AS receita_q3,
       ROUND(
           (SUM(CASE WHEN SUBSTR(dt_venda,6,2) IN ('07','08','09') THEN vl_total_venda ELSE 0 END) -
            SUM(CASE WHEN SUBSTR(dt_venda,6,2) IN ('04','05','06') THEN vl_total_venda ELSE 0 END)) * 100.0 /
           NULLIF(SUM(CASE WHEN SUBSTR(dt_venda,6,2) IN ('04','05','06') THEN vl_total_venda ELSE 0 END), 0),
       1) AS variacao_pct
FROM venda_parquet
WHERE SUBSTR(dt_venda,1,4) = '2024'
GROUP BY nm_produto
HAVING receita_q2 > 0
ORDER BY variacao_pct ASC
LIMIT 20""",
        "Compara receita por produto entre Q2 e Q3 de 2024, mostrando a variação percentual.",
    ),
    # Vendas por estado
    (
        ["estado"],
        """SELECT nm_filial,
       COUNT(*) AS total_vendas,
       ROUND(SUM(vl_total_venda), 2) AS receita_total
FROM venda_parquet
GROUP BY nm_filial
ORDER BY receita_total DESC""",
        "Agrega receita total e número de vendas por filial.",
    ),
    # Clientes por cidade/estado
    (
        ["cliente", "cidade"],
        """SELECT ct_cidade,
       sg_estado,
       COUNT(*) AS total_clientes
FROM cliente_parquet
GROUP BY ct_cidade, sg_estado
ORDER BY total_clientes DESC""",
        "Conta o total de clientes cadastrados por cidade e estado.",
    ),
    # Default fallback — receita total por filial
    (
        [],
        """SELECT nm_filial,
       COUNT(*) AS total_vendas,
       ROUND(SUM(vl_total_venda), 2) AS receita_total
FROM venda_parquet
GROUP BY nm_filial
ORDER BY receita_total DESC""",
        "Agrega receita total e número de vendas por filial.",
=======
# All SQL is written to run against the SQLite mock schema:
#   sales(sale_id, region, product_id, amount, quantity, sale_date, channel)
#   products(product_id, name, category, unit_price, cost_price, is_active)
#   customers(customer_id, name, email, region, segment, created_at)
#   orders(order_id, customer_id, order_date, status, total_amount)
# ---------------------------------------------------------------------------

_MOCK_SCENARIOS: list[tuple[list[str], str, str]] = [
    # Top customers by revenue
    (
        ["top", "customer", "revenue"],
        """SELECT c.name AS customer_name,
       c.region,
       c.segment,
       SUM(o.total_amount) AS total_revenue
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name, c.region, c.segment
ORDER BY total_revenue DESC
LIMIT 10""",
        "Returns the top 10 customers ranked by total order revenue.",
    ),
    # Average ticket / average order value by channel
    (
        ["average", "ticket", "channel"],
        """SELECT channel,
       ROUND(AVG(CAST(amount AS REAL)), 2) AS avg_ticket,
       COUNT(*) AS total_sales
FROM sales
GROUP BY channel
ORDER BY avg_ticket DESC""",
        "Calculates the average sale amount (ticket) and total number of sales for each channel.",
    ),
    # Churn rate / churned customers
    (
        ["churn"],
        """SELECT segment,
       COUNT(*) AS total_customers,
       SUM(CASE WHEN churned = 1 THEN 1 ELSE 0 END) AS churned_customers,
       ROUND(100.0 * SUM(CASE WHEN churned = 1 THEN 1 ELSE 0 END) / COUNT(*), 1) AS churn_rate_pct
FROM (
    SELECT c.customer_id,
           c.segment,
           CASE WHEN MAX(o.order_date) < DATE(julianday('now') - 90) THEN 1 ELSE 0 END AS churned
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id, c.segment
) sub
GROUP BY segment
ORDER BY churn_rate_pct DESC""",
        "Estimates churn rate per customer segment by flagging customers with no order in the last 90 days.",
    ),
    # Critical stock / low stock / inventory
    (
        ["stock", "critical"],
        """SELECT p.name AS product_name,
       p.category,
       p.unit_price,
       COALESCE(SUM(CAST(s.quantity AS INTEGER)), 0) AS units_sold
FROM products p
LEFT JOIN sales s ON p.product_id = s.product_id
WHERE CAST(p.is_active AS TEXT) = 'True'
GROUP BY p.product_id, p.name, p.category, p.unit_price
HAVING units_sold > 0
ORDER BY units_sold DESC
LIMIT 20""",
        "Lists active products with their total units sold, highlighting the most-moved inventory.",
    ),
    # Delinquency / overdue / pending payments
    (
        ["delinquency"],
        """SELECT status,
       COUNT(*) AS order_count,
       ROUND(SUM(CAST(total_amount AS REAL)), 2) AS total_value
FROM orders
GROUP BY status
ORDER BY total_value DESC""",
        "Breaks down orders by status to surface pending and overdue payment totals.",
    ),
    # Sales by product / product performance
    (
        ["product", "sales"],
        """SELECT p.name AS product_name,
       p.category,
       COUNT(s.sale_id) AS num_sales,
       SUM(CAST(s.quantity AS INTEGER)) AS units_sold,
       ROUND(SUM(CAST(s.amount AS REAL)), 2) AS total_revenue
FROM sales s
JOIN products p ON s.product_id = p.product_id
GROUP BY p.product_id, p.name, p.category
ORDER BY total_revenue DESC""",
        "Shows total revenue and units sold per product, joined with product metadata.",
    ),
    # Sales drop / Q3 vs Q2 comparison
    (
        ["drop", "q3", "q2"],
        """SELECT p.name AS product_name,
       ROUND(SUM(CASE WHEN strftime('%m', s.sale_date) IN ('04','05','06') THEN CAST(s.amount AS REAL) ELSE 0 END), 2) AS q2_revenue,
       ROUND(SUM(CASE WHEN strftime('%m', s.sale_date) IN ('07','08','09') THEN CAST(s.amount AS REAL) ELSE 0 END), 2) AS q3_revenue,
       ROUND(
           (SUM(CASE WHEN strftime('%m', s.sale_date) IN ('07','08','09') THEN CAST(s.amount AS REAL) ELSE 0 END) -
            SUM(CASE WHEN strftime('%m', s.sale_date) IN ('04','05','06') THEN CAST(s.amount AS REAL) ELSE 0 END)) * 100.0 /
           NULLIF(SUM(CASE WHEN strftime('%m', s.sale_date) IN ('04','05','06') THEN CAST(s.amount AS REAL) ELSE 0 END), 0),
       1) AS pct_change
FROM sales s
JOIN products p ON s.product_id = p.product_id
WHERE strftime('%Y', s.sale_date) = '2024'
GROUP BY p.product_id, p.name
HAVING q2_revenue > 0
ORDER BY pct_change ASC
LIMIT 20""",
        "Compares Q2 vs Q3 2024 revenue per product and calculates the percentage change, ordered by largest drop.",
    ),
    # Sales by region
    (
        ["sales", "region"],
        """SELECT region,
       COUNT(*) AS num_sales,
       ROUND(SUM(CAST(amount AS REAL)), 2) AS total_sales,
       ROUND(AVG(CAST(amount AS REAL)), 2) AS avg_sale
FROM sales
GROUP BY region
ORDER BY total_sales DESC""",
        "Aggregates total and average sales by region.",
    ),
    # Orders by status
    (
        ["order", "status"],
        """SELECT status,
       COUNT(*) AS total_orders,
       ROUND(SUM(CAST(total_amount AS REAL)), 2) AS total_value,
       ROUND(AVG(CAST(total_amount AS REAL)), 2) AS avg_order_value
FROM orders
GROUP BY status
ORDER BY total_orders DESC""",
        "Summarises order counts and values grouped by order status.",
    ),
    # Revenue by category
    (
        ["category", "revenue"],
        """SELECT p.category,
       COUNT(s.sale_id) AS num_sales,
       ROUND(SUM(CAST(s.amount AS REAL)), 2) AS total_revenue
FROM sales s
JOIN products p ON s.product_id = p.product_id
GROUP BY p.category
ORDER BY total_revenue DESC""",
        "Shows total revenue and sale count broken down by product category.",
    ),
    # Default fallback — total sales by region
    (
        [],
        """SELECT region,
       COUNT(*) AS num_sales,
       ROUND(SUM(CAST(amount AS REAL)), 2) AS total_sales
FROM sales
GROUP BY region
ORDER BY total_sales DESC""",
        "Aggregates total sales by region.",
>>>>>>> a749ebc84c4475b1a91e44c8818945562ebe6f32
    ),
]


def _mock_response(query: str) -> LLMResult:
    """
    Returns a question-aware mock LLMResult.

    If the natural-language query expresses destructive intent (DELETE, DROP,
    INSERT, UPDATE, etc.), returns an empty SQL with a refusal explanation —
    matching the behaviour that the real LLM is instructed to follow via
    system-prompt rule #3.

    Otherwise, matches the query against _MOCK_SCENARIOS by keyword presence
    and returns the first matching SQL + explanation pair.
    Used when WATSONX_MOCK=True or when the API is unreachable.
    """
    if _is_destructive_intent(query):
        return LLMResult(
            sql="",
            explanation=(
                "I can only run read-only analytical queries. "
                "Data modification and DDL operations (DELETE, DROP, INSERT, "
                "UPDATE, ALTER, TRUNCATE, etc.) are not permitted."
            ),
        )

    q_lower = query.lower()
    for keywords, sql, explanation in _MOCK_SCENARIOS:
        if all(kw in q_lower for kw in keywords):
            return LLMResult(
                sql=sql,
                explanation=f"[MOCK] {explanation}",
            )
    # Should never reach here because the last scenario has empty keywords (always matches)
    return LLMResult(
        sql=_MOCK_SCENARIOS[-1][1],
        explanation=f"[MOCK] {_MOCK_SCENARIOS[-1][2]}",
    )


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def build_prompt(llm_request: LLMRequest, schema: Optional[SchemaContext] = None) -> str:
    """
    Build the prompt sent to the watsonx.ai endpoint.

    If a SchemaContext is provided, delegates to build_context_prompt() for
    schema-aware prompting (higher SQL accuracy).
    Falls back to the generic system prompt when no schema is available.

    Args:
        llm_request: The LLM request containing the natural language query.
        schema:      Optional schema context loaded from schema.json.

    Returns:
        A single prompt string ready to be sent to the LLM.
    """
    if schema is not None:
        from app.services.schema_service import build_context_prompt
        return build_context_prompt(schema, llm_request.natural_language_query)
    return _SYSTEM_PROMPT_FALLBACK.format(query=llm_request.natural_language_query)


# ---------------------------------------------------------------------------
# Real API call
# ---------------------------------------------------------------------------

async def _call_watsonx_api(prompt: str) -> str:
    """
    POST to the watsonx.ai text-generation endpoint and return the raw
    generated text string.

    Raises httpx.HTTPStatusError on non-2xx responses.
    """
    url = f"{settings.WATSONX_URL}/ml/v1/text/generation?version=2023-05-29"
    headers = {
        "Authorization": f"Bearer {settings.WATSONX_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "model_id": settings.WATSONX_MODEL_ID,
        "project_id": settings.WATSONX_PROJECT_ID,
        "input": prompt,
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": settings.WATSONX_MAX_NEW_TOKENS,
            "temperature": settings.WATSONX_TEMPERATURE,
            "stop_sequences": ["}"],
        },
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()

    data = response.json()
    # watsonx response envelope: results[0].generated_text
    generated_text: str = data["results"][0]["generated_text"]
    # The stop_sequence "}" is consumed — re-append it so we get valid JSON
    return generated_text.strip() + "}"


# ---------------------------------------------------------------------------
# Response parser
# ---------------------------------------------------------------------------

def _parse_llm_output(raw_text: str, original_query: str) -> LLMResult:
    """
    Parse the raw model output into an LLMResult.
    Falls back to a safe error result if parsing fails.
    """
    try:
        data = json.loads(raw_text)
        sql = data.get("sql", "").strip()
        explanation = data.get("explanation", "").strip()

        if not _is_safe_sql(sql):
            logger.warning("LLM returned a forbidden SQL verb — rejecting", extra={"sql": sql})
            return LLMResult(
                sql="",
                explanation=(
                    "The generated query contained disallowed operations "
                    "(DELETE / UPDATE / DROP, etc.) and was rejected for safety."
                ),
            )

        return LLMResult(sql=sql, explanation=explanation)

    except (json.JSONDecodeError, KeyError) as exc:
        logger.error("Failed to parse LLM output", exc_info=exc, extra={"raw": raw_text})
        return LLMResult(
            sql="",
            explanation=(
                "The model returned an unstructured response that could not be parsed. "
                f"Original query: '{original_query}'"
            ),
        )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def generate_sql(
    llm_request: LLMRequest,
    schema: Optional[SchemaContext] = None,
) -> LLMResult:
    """
    Main entry point called by QueryService.

    If WATSONX_MOCK is True (default for local dev), returns a mock result.
    Otherwise calls the real watsonx.ai API and parses the response.

    Args:
        llm_request: The LLM request with the natural language query.
        schema:      Optional SchemaContext for schema-aware prompting.
    """
    if settings.WATSONX_MOCK:
        logger.info("WATSONX_MOCK=True — returning mock LLM response")
        return _mock_response(llm_request.natural_language_query)

    # Guard: refuse destructive intent before sending to the real LLM
    if _is_destructive_intent(llm_request.natural_language_query):
        logger.info(
            "Destructive intent detected — refusing before LLM call",
            extra={"query": llm_request.natural_language_query},
        )
        return LLMResult(
            sql="",
            explanation=(
                "I can only run read-only analytical queries. "
                "Data modification and DDL operations (DELETE, DROP, INSERT, "
                "UPDATE, ALTER, TRUNCATE, etc.) are not permitted."
            ),
        )

    prompt = build_prompt(llm_request, schema=schema)
    logger.debug(
        "Sending prompt to watsonx",
        extra={"model": settings.WATSONX_MODEL_ID, "schema_aware": schema is not None},
    )

    try:
        raw_text = await _call_watsonx_api(prompt)
        return _parse_llm_output(raw_text, llm_request.natural_language_query)
    except httpx.HTTPStatusError as exc:
        logger.error(
            "watsonx API returned an error",
            exc_info=exc,
            extra={"status_code": exc.response.status_code},
        )
        raise
