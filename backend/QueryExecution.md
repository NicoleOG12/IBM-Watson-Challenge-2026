You are a backend engineer.

Create a query execution service.

Requirements:
- Accept a validated SQL query
- Execute it using:
  - Option A: mock dataset (CSV or in-memory)
  - Option B: pluggable connector (future BigQuery/Redshift)
- Return results as JSON

Include:
- Example dataset
- Function execute_query(sql)
- Error handling