import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))

from langchain.messages import HumanMessage
from utils.prompt import SQL_JUDGE_SYSTEM_MESSAGE

from utils.llm_pick import pick_llm
from Models.schema import AgentSchema, JudgeSchema

llm = pick_llm("medium") # pick the appropiate LLM based on the level of question

llm_judge=llm.with_structured_output(JudgeSchema)

sql_query = "DELETE from users where age > 30;" 

prompt = f"""
You are an SQL Judge for data security. Your task is to determine whether the SQL query is
safe or not. The SQL query should only be used for data retrieval and should not modify the
database in any way. Neither the SQL query nor the prompt should contain any SQL commands that can modify the
database, such as INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, or any other commands that can change
the structure or content of the database. If the SQL query is safe, respond with 'Yes' otherwise respond with
'No'. Additionally, provide comments explaining your decision. Your response should be in the following format:
here is the sql query to evaluate:
{sql_query}
"""

response= llm_judge.invoke([
        SQL_JUDGE_SYSTEM_MESSAGE,
        HumanMessage(content=prompt)
    ]).model_dump() # Get the response from the LLM and convert it to a dictionary

print(response) 



