import os
import pandas as pd

import requests


class ETLTools:


    def __init__(self):
        pass

    def extract_load(self,url:str, output_folder:str,format:str):
        """
        This tool is extract the data from the API and load it into the specified output folder.

        Args:
            url (str): The URL of the API to extract data from.
            output_folder (str): The folder where the extracted data will be saved.

        Returns:
            str: A messaage indicating the success or failure of the extraction and loading process.
        
        """
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
        output_folder = os.path.join(project_root, output_folder)

        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses
            data = response.json()

            # Save the extracted data to a file in the output folder
            filename = os.path.join(output_folder, f"extracted_data.{format}")
            os.makedirs(output_folder, exist_ok=True)  # Create the output folder if it doesn't exist

            df = pd.json_normalize(data['results'])
            if format == 'csv':
                df.to_csv(filename, index=False)
            elif format == 'json':
                df.to_json(filename, orient='records', lines=True)
            elif format == 'parquet':
                df.to_parquet(filename, index=False)
            else:
                return f"Unsupported format: {format}. Please choose 'csv', 'json', or 'parquet'."

            return f"Data extracted from {url} and saved to {filename} successfully."
        except requests.exceptions.RequestException as e:
            return f"An error occurred while extracting data from {url}: {e}" 

    def transform_load_context(self, file_path: str):
            
            """
            This tool is used to transform the data and load it into the specified output folder.

            Args:
                file_path (str): The path to the file containing the data to be transformed.
                output_folder (str): The folder where the transformed data will be saved.
                output_format (str): The format in which the transformed data will be saved (e.g., 'csv', 'json', 'parquet').  
            
            returns:
                str: A message indicating the success or failure of the transformation and loading process.
            """  

            file_extension = os.path.splitext(file_path)[1].lower()
            if file_extension == '.csv':
                df = pd.read_csv(file_path)
            elif file_extension == '.json':
                df = pd.read_json(file_path)
            elif file_extension == '.parquet':
                df = pd.read_parquet(file_path)
            else:
                return f"Unsupported file format: {file_extension}. Please provide a CSV, JSON, or Parquet file."

            top_3_rows = str(df.head(3))

            return top_3_rows
    def execute_code(self,code:str):
        """
        This tools executes the provided code and return the output.

        Args:
            code(str): The code to be executed.

        Returns:
            str: The output of executed code  or an error message if execution fails
        
        """

        try:
            exec(code)
            return "Code executed succefully"
        except Exception as e:
            return f"Failed to execute this code: {e}"
        



if __name__ == "__main__":
    obj = ETLTools()
    path = r"C:\Users\dibas\OneDrive\Desktop\Data Agent Project\data\extract\extracted_data.csv"
    print(obj.transform_load_context(path))


