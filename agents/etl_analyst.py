import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.llm_pick import pick_llm
from utils.etl_tools import ETLTools
from Models.schema import ETLAgentSchema
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langchain.tools import tool
from langchain_openai  import ChatOpenAI

#--------------------------------Agent Tools-------------------------------------------------------
@tool
def extract_load_tool(url:str, output_folder:str,format:str)-> str:

    """
            This tool is extract the data from the API and load it into the specified output folder.
    
            Args:
                url (str): The URL of the API to extract data from.
                output_folder (str): The folder where the extracted data will be saved.
    
            Returns:
                str: A messaage indicating the success or failure of the extraction and loading process.
            
    """
    etl_tools = ETLTools()
    return etl_tools.extract_load(url,output_folder,format)

@tool
def transform_load_tool(input_filepath:str, output_folder:str,output_format:str,user_question:str)-> str:

    """
            This tool is extract the data from the API and load it into the specified output folder.
    
            Args:
                url (str): The URL of the API to extract data from.
                output_folder (str): The folder where the extracted data will be saved.
    
            Returns:
                str: A messaage indicating the success or failure of the extraction and loading process.
            
    """
    etl_tools = ETLTools()

    top_3_rows = etl_tools.transform_load_context(input_filepath)

    llm = pick_llm('high')

    prompt = f"""
            You are a Python Data Analyst who uses Pandas to analyze data. 
            You need to provide only the Pandas Code that will help to perform the right ETL operations on the data stored in the file : {input_filepath}
            as per the user's question. Do not provide any explanation or comments, only
            the code should be provided. The code should be in a format that can be executed 
            in a Python environment with Pandas installed. 
            Don't write anything else than Pandas Code. \n
            
            Create the Pandas Dataframe from the data stored in the file : {input_filepath} and then 
            write the code to transform and save the data at {output_folder}.
            Here's the user's question: {user_question}\n
            Here's the context of the data you will be analyzing: {top_3_rows}\n

        """
    response = llm.invoke(prompt).content 

    # Optional Cleaning
    pandas_code = "".join(item["text"] if isinstance(item, dict) and "text" in item else item if isinstance(item, str) else "" for item in response).strip().strip('```').strip().lstrip('python').strip()

    # Execute the Pandas code
    results = etl_tools.execute_code(pandas_code)

    return f"The data is transformed and saved at {output_folder} in {output_format} format. \n\n Pandas Code Executed: \n {pandas_code} \n\n Execution Result: \n {results}"

#ToolKit
tools = [extract_load_tool,transform_load_tool]

llm = pick_llm('high')
llm_bind = llm.bind_tools(tools)

#---------------------------------------------------- Agent Graph --------------------------------------------------------


def llm_node(state:ETLAgentSchema):
    messages=state.messages

    prompt = f"""
            You are a Python Data Analyst who has access to tools that can extract and load, 
            transform and load data. You will be provided with a user's question 
            and you would need to perform the right ETL operations as per the user's question. 
            If the operation is performed then inform the user and end the coversation.
            Here's the chat history: {messages}\n
    """

    final_answer = llm_bind.invoke(prompt)

    state.messages= messages + [final_answer]

    return state

def tool_node(state:ETLAgentSchema):
    """
    This node is responsible for invoking the appropiate tool based on the user's question.
    """
    tools_results=[]

    tools_by_name = {tool.name: tool for tool in tools}

    tool_calls = state.messages[-1].tool_calls

    for tool_call in tool_calls:

        tool = tools_by_name[tool_call['name']]
        observation = tool.invoke(tool_call['args'])

        tools_results.append(ToolMessage(content=observation, tool_call_id = tool_call['id']))

    state.messages = state.messages + tools_results

    return state   

    # Nodes & Edges
etl_analyst_graph = StateGraph(ETLAgentSchema)
etl_analyst_graph.add_node("llm_node", llm_node)
etl_analyst_graph.add_node("tool_node", tool_node)

etl_analyst_graph.add_edge(START, "llm_node")

def is_tool_call(state:ETLAgentSchema):
    tool_calls = state.messages[-1].tool_calls

    if tool_calls:
        return "tool_node"
    else:
        return "end"

etl_analyst_graph.add_conditional_edges(
    "llm_node",is_tool_call,
    {
        "tool_node": "tool_node",
        "end": END
    }
)

etl_analyst_graph.add_edge("tool_node", "llm_node")


# Compile the Graph
etl_analyst = etl_analyst_graph.compile()


if __name__ == "__main__":

    from IPython.display import Image

    img = Image(etl_analyst.get_graph().draw_mermaid_png())

    with open("etl_analyst_graph.png", "wb") as f:
        f.write(img.data)

    # response = etl_analyst.invoke(
    #     {
    #         "messages": [
    #             HumanMessage(
    #                 content=(
    #                     "Extract data from "
    #                     "https://pokeapi.co/api/v2/pokemon "
    #                     "and save it as CSV in the folder "
    #                     "data/extract/csv. "
    #                     "Use format='csv'."
    #                 )
    #             )
    #         ]
    #     }
    # )
if __name__ == "__main__":
    response = etl_analyst.invoke(
        {
            "messages": [
                HumanMessage(
                    content="""
                    Transform the data stored in:
                    'data/extract/csv/extracted_data.csv'

                    Save the transformed data in:
                    'data/transform'

                    Output format: CSV.

                    Transformation requirement:
                    Filter the data to show only Bulbasaur Pokemon.

                    Create the output directory if it does not exist.
                    Save the transformed file as 'transformed_data.csv'.
                    """
                )
            ]
        }
    )

    print(response)