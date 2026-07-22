You are a backend engineer focused on security.

Create a SQL validation module.

Requirements:
- Accept a SQL string
- Validate that:
  - Only SELECT statements are allowed
  - No DELETE, UPDATE, INSERT, DROP
- Reject queries with multiple statements
- Return:
  - valid: true/false
  - reason: explanation

Include:
- Regex or parsing logic
- Unit test examples