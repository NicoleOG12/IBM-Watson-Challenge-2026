You are an AI engineer.

Extend the existing FastAPI backend to integrate with IBM watsonx (Bob).

Requirements:
- Create a service layer to send prompts to the LLM
- The LLM must:
  1. Understand a natural language query
  2. Generate a SQL query (SELECT only)
- Add prompt engineering to enforce:
  - No DELETE, UPDATE, DROP
  - Only analytical queries
- Return structured output:
  {
    "sql": "...",
    "explanation": "..."
  }

Include:
- Example prompt sent to the LLM
- Function to call the model
- Mock response (if API not available)