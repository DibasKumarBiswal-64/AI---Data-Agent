# AI Data Agent — Multi-Agent SQL & ETL Automation

This project explores how LLMs can make database querying easier by allowing users to ask questions in natural language instead of writing SQL manually.

The SQL agent uses LangGraph to manage the workflow, LangChain to interact with LLMs, and PostgreSQL to retrieve data. It uses the database schema as context to generate SQL, evaluates the generated query, executes approved queries, and converts the results into a user-friendly response.

## Features

- Convert natural language questions into PostgreSQL queries.
- Retrieve database schema details to provide context for SQL generation.
- Evaluate generated SQL queries using an LLM with structured output.
- Use conditional routing in LangGraph to handle approved and rejected queries.
- Execute approved queries and pass the results to the response-generation step.
- Generate concise answers based on database results.
- Extend the agent with data processing and ETL workflows.

## Workflow
mermaid
flowchart TD
    A[User Question] --> B[Curate Question]
    B --> C[Retrieve Database Schema]
    C --> D[Generate SQL Query]
    D --> E[Evaluate SQL Safety]
    E --> F{Approved?}
    F -->|Yes| G[Execute SQL]
    F -->|No| H[Reject Query]
    G --> I[Generate Final Answer]
    H --> J[Return Response]
    I --> J


## Tech Stack

- Python
- LangChain
- LangGraph
- Pydantic
- PostgreSQL
- Pandas

## How it works

1. The user submits a question in natural language.
2. The agent refines the question and retrieves the database schema.
3. An LLM generates a PostgreSQL query using the question and schema.
4. Another LLM call evaluates whether the generated query is safe.
5. LangGraph routes the query to the execution or rejection node.
6. The execution node retrieves the database results.
7. The final node converts the results into a natural language answer.

## Getting Started

### Clone the repository


git clone https://github.com/DibasKumarBiswal-64/AI---Data-Agent.git
cd AI---Data-Agent


### Create a virtual environment

Using Windows Command Prompt:

py -3.12 -m venv .venv
.venv\Scripts\activate


### Install dependencies


python -m pip install --upgrade pip
pip install -r requirements.txt


### Configure environment variables

Create a `.env` file in the project root with your PostgreSQL connection details and LLM API credentials.

dotenv
host=localhost
port=5432
user=your_read_only_db_user
password=your_database_password
database=your_database_name

OPENAI_API_KEY=your_api_key


Use the variable names expected by your configuration. Ensure the application loads the `.env` file before reading these values.

Never commit API keys or database credentials to GitHub.

### Run the SQL agent


python agents\sql_analyst.py


Make sure PostgreSQL is running and your database contains the tables required by the query.

## Example

**Question**

What are the different types of payment methods in our database?


**Generated SQL**


SELECT DISTINCT payment_method
FROM public.payments
WHERE payment_method IS NOT NULL
ORDER BY payment_method
LIMIT 10;


The agent evaluates the generated query before execution. If approved, it retrieves the results from PostgreSQL and generates a natural language response.

The actual output depends on the data available in the database.

## Improvements to Work On

- Add SQL parsing and deterministic validation before execution.
- Enforce read-only database permissions.
- Improve handling of LLM errors, database failures, and timeouts.
- Add automated tests for SQL generation and conditional routing.
- Introduce query execution limits and result-size controls.
- Evaluate SQL accuracy and the quality of generated answers.
- Extend the agent with additional ETL workflows and API integration.

The LLM safety check is one part of the workflow, not a standalone security mechanism. Database permissions and server-side validation are also necessary for safe execution.



