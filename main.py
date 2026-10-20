from agents.data_agent import data_agent
from langchain_core.messages import HumanMessage

if __name__ == "__main__":

    response = data_agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content="Extract the data from the API endpoint 'https://pokeapi.co/api/v2/pokemon' and save it to the 'data/extract' folder in CSV format as 'extracted_data.csv'. Create the output directory if it does not exist."
                )
            ],
            "route_response": ""
        }
    )

    print(response)