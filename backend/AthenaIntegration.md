We already have an endpoint that takes a question, generates SQL, and executes it using a mock dataset (mock_data.py). Now we want to integrate with AWS Athena while keeping a local fallback.

Goal
Build a query execution layer with:

Athena support (production)
Mock fallback (local/dev)
A plugable interface (so we don’t break existing code)

Technical Requirements
1. Base Interface

Create an abstract class like:

class QueryExecutor:
    def execute(self, sql: str) -> dict:
        pass
2. MockExecutor
Use MOCK_TABLES from mock_data.py
Return:
{
  "columns": [...],
  "rows": [...]
}
Can be simple (no need for full SQL parsing)
3. AthenaExecutor

Use boto3 and implement:

start_query_execution
polling until completion
get_query_results

Important:

handle errors (FAILED / CANCELLED)
parse results (header + rows)
return same format as mock
4. Factory with fallback

Something like:

def get_executor():
    if USE_ATHENA:
        try:
            return AthenaExecutor(...)
        except:
            return MockExecutor()
    return MockExecutor()
5. Environment Variables

Support:

USE_ATHENA
ATHENA_DB
ATHENA_OUTPUT
AWS_REGION

Nice-to-have (if you have time)
query execution time
data scanned (Athena stats)
estimated cost (based on bytes scanned)

Expected Output

We want something like:

{
  "sql": "...",
  "result": {
    "columns": [...],
    "rows": [...]
  },
  "metadata": {
    "execution_time_ms": 1234,
    "rows_returned": 100,
    "data_scanned_bytes": 123456,
    "estimated_cost_usd": 0.0023
  }
}

Important Note
The idea is:

run locally with mock
switch to Athena in production via a flag

without changing the rest of the code

You can organize it like:

services/execution/