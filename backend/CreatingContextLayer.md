You are a data engineer.

Create a schema management module for the backend.

Requirements:
- Store metadata for tables:
  - table_name
  - columns
  - descriptions
- Load this metadata from a JSON file
- Create a function that injects this schema into the LLM prompt context

Goal:
Improve SQL generation accuracy using schema-aware prompting.

Return:
- JSON example
- Python module to load schema
- Function: build_context_prompt(schema, user_query)