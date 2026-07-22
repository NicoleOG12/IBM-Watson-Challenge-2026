You are a backend engineer.

Create a conversation memory module.

Requirements:
- Store conversation history per user_id
- Keep:
  - previous queries
  - generated SQL
- Use in-memory storage (dict) for MVP
- Provide function:
  - get_context(user_id)
  - save_interaction(user_id, query, sql)

Goal:
Allow follow-up questions like:
"What about last month?"