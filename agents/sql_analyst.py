import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))

from langchain_core.messages import AIMessage, HumanMessage
from utils.database import DatabaseUtil
from utils.llm_pick import pick_llm
from Models.schema import AgentSchema, JudgeSchema
from langgraph.graph import StateGraph, START,END

#------------------------------------ AI Agent Code ---------------------------------------

def curate_ques(state:AgentSchema) -> AgentSchema:
    user_question = state.user_question
    llm = pick_llm("low") # pick the appropiate LLM based on the level of question

    response=llm.invoke(f"Curate the following question: {user_question}").content

    if isinstance(response, list):
        response = "".join(
            item["text"] for item in response
            if isinstance(item, dict) and "text" in item
        )

    state.curated_ques = response

    state.message = state.message + [HumanMessage(content=f"{response}")] # Append the curated question to the message list

    return state

def prompt_query_context(state: AgentSchema) -> AgentSchema:

    curated_question = state.curated_ques

    conn_details = {
        "host": os.environ["host"],
        "port": os.environ["port"],
        "user": os.environ["user"],
        "password": os.environ["password"],
        "dbname": os.environ["database"]

    }

    obj = DatabaseUtil(conn_details)
    schema_info = obj.schema_details("public") # Fetch the schema details from the database

    # Constructing the prompt query for the agent to generate the SQL query
    prompt = f"""
    You are an SQL analyst agent. Your task is to convert the user's natural language 
    query into Postgres SQL query that can be executed on the database. You are provided 
    with the user's original query and the schema details of the database, including
    table names, column names, data types, and sample data for each table so that 
    you can understand the structure of the database and generate an accurate SQL query.
    Unless user explicitly asks for specific number of rows, always limit the output to 10 rows.
    Note - Just generate the SQL query without any explanation or additional text because
    this query will be executed directly on the database. So, the output should be SQL
    ready to be executed without any modifications.  
    
    User's Original Query: {curated_question}

    Database Schema Details:
    {schema_info}
    
    """   
    state.prompt_query_context = prompt

    return state



def generate_sql_query(state: AgentSchema) -> AgentSchema:
    prompt = state.prompt_query_context

    llm = pick_llm("medium") # pick the appropiate LLM based on the level of question
    generated_sql_query = llm.invoke(prompt).content # Generate the SQL query using the prompt

    if isinstance(generated_sql_query, list):
        generated_sql_query = "".join(
            item["text"] if isinstance(item, dict) and "text" in item
            else item if isinstance(item, str)
            else ""
            for item in generated_sql_query
        )
    state.generated_sql_query = generated_sql_query.strip() # Remove any leading or trailing whitespace from the generated SQL query

    return state







#Is Safe node

def is_safe_sql(state: AgentSchema) -> AgentSchema:

    sql_query = state.generated_sql_query

    llm = pick_llm("medium") # pick the appropiate LLM based on the level of question

    llm_judge=llm.with_structured_output(JudgeSchema)

    prompt = f"""
    You are an SQL Judge for data security. Your task is to determine whether the SQL query is
    safe or not. The SQL query should only be used for data retrieval and should not modify the
    database in any way. Neither the SQL query nor the prompt should contain any SQL commands that can modify the
    database, such as INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, or any other commands that can change
    the structure or content of the database. If the SQL query is safe, respond with 'Yes' otherwise respond with
    'No'. Additionally, provide comments explaining your decision.
    Here's the SQL query to evaluate:
    {sql_query}"""

    response= llm_judge.invoke(prompt).model_dump() # Get the response from the LLM and convert it to a dictionary
    
    state.is_safe = response['answer']
    state.comments = response['comments']

    return state


#Cancle SQL Query Node
def cancle_sql(state: AgentSchema) -> AgentSchema:
    comments = state.comments
    state.final_answer = f"The generated SQL query is not safe to execute. Reason: {comments}. Therefore, the SQL query will not be executed."
    state.message = state.message + [AIMessage(content=f"{state.final_answer}")] # Append the final answer to the message list
    return state

# Execute SQL Query
def execute_sql(state: AgentSchema) -> AgentSchema:
    sql_query = state.generated_sql_query

    conn_details = {
        "host": os.environ["host"],
        "port": os.environ["port"],
        "user": os.environ["user"],
        "password": os.environ["password"],
        "dbname": os.environ["database"]

    }

    obj = DatabaseUtil(conn_details)
    execution_result = obj.execute_sql(sql_query) # Execute the SQL query on the database

    state.sql_query_execution_result = execution_result

    return state

# Represent Final Answer Node
def represent_final_answer(state: AgentSchema) -> AgentSchema:

    execution_result = state.sql_query_execution_result
    curated_question = state.curated_ques

    llm = pick_llm("medium") # pick the appropiate LLM based on the level of question

    prompt = f"""
    You are an SQL analyst agent. Your task is to generate a final answer for the user based on the 
    SQL query execution result and the user's original question. The final answer should be concise, 
    clear, and directly address the user's query. Avoid including any SQL code or technical details 
    in the final answer. If the SQL query execution result is empty or does not provide relevant 
    information, inform the user accordingly.\n
    
    User's Original Query: {curated_question}\n
    
    SQL Query Execution Result: {execution_result}
    
    Please provide a final answer for the user based on the above information.
    """

    llm_response= llm.invoke(prompt).content # Generate the final answer using the prompt

    state.final_answer = llm_response   
    state.message = state.message + [AIMessage(content=f"{llm_response}")] # Append the final answer to the message list

    return state


#Conditional edge function
def is_safe_sql_query(state: AgentSchema) -> str:
    is_safe=state.is_safe.strip()

    if is_safe == "Yes":
        return "execute_sql"
    else:
        return "cancle_sql"



#---------------------------------------- Graph Building ----------------------------------------

sql_agent_graph = StateGraph(AgentSchema)

#Nodes
sql_agent_graph.add_node(curate_ques, name="Curate Question")
sql_agent_graph.add_node(prompt_query_context, name="Prompt Query Context")
sql_agent_graph.add_node(generate_sql_query, name="Generate SQL Query") 
sql_agent_graph.add_node(is_safe_sql, name="Is Safe SQL Query?")
sql_agent_graph.add_node(cancle_sql, name="Cancel SQL Query")  
sql_agent_graph.add_node(execute_sql, name="EXECUTE_SQL") 
sql_agent_graph.add_node(represent_final_answer, name="Represent Final Answer")

#Edges
sql_agent_graph.add_edge(START, "curate_ques")
sql_agent_graph.add_edge("curate_ques", "prompt_query_context")
sql_agent_graph.add_edge("prompt_query_context", "generate_sql_query")
sql_agent_graph.add_edge("generate_sql_query", "is_safe_sql")

sql_agent_graph.add_conditional_edges(
    "is_safe_sql",
    is_safe_sql_query,
    {
        "execute_sql": "execute_sql",
        "cancle_sql": "cancle_sql"
    }
)

# sql_agent_graph.add_edge("is_safe_sql","cancle_sql")
# sql_agent_graph.add_edge("is_safe_sql", "execute_sql")


sql_agent_graph.add_edge("cancle_sql", END)

sql_agent_graph.add_edge("execute_sql", "represent_final_answer")
sql_agent_graph.add_edge("represent_final_answer", END)

 # Compile the graph 
sql_analyst_agent = sql_agent_graph.compile()

if __name__ == "__main__":
   


    from IPython.display import Image, display
    img = Image(sql_analyst_agent.get_graph().draw_mermaid_png())
    with open("sql_analyst_agent_graph.png", "wb") as f:
        f.write(img.data)



    input_schema = {
        "message": [],
        "user_question": "What are the different types of payment method wehave in our database",
        "curated_ques": "",
        "prompt_query_context": "",
        "generated_sql_query": "",
        "is_safe": "No",
        "comments": "",
        "sql_query_execution_result": "",
        "final_answer": ""

    }


    # Execute the agent with the input schema
    sql_analyst_response=sql_analyst_agent.invoke(input_schema)
    print(sql_analyst_response['message'])  # Print the final answer generated by the agent
    print('******************************************')

    print(sql_analyst_response['generated_sql_query'])  # Print the generated SQL query
    print('******************************************')

    print(sql_analyst_response['sql_query_execution_result'])  # Print the SQL query execution result

    print('******************************************')

    print(sql_analyst_response['prompt_query_context'])  # Print the prompt query context used to generate the SQL query








