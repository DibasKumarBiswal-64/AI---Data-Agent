import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

class DatabaseUtil:

    def __init__(self,db_config):
        self.db_config=db_config


        try:
            self.connection = psycopg2.connect(**db_config)
        except Exception as e:
            print(f"Error connection to the database: {e}")
            self.connection=None

    def schema_details(self,schema_name):
        schema_info_context= ""
        connection= self.connection
        cursor=connection.cursor()
        schema_info_context = f"Database Schema: {schema_name}\n"

        try:
            cursor.execute("select table_name from information_schema.tables where table_schema=%s;",(schema_name,))
            tables_list = cursor.fetchall()

            for table in tables_list:
                table_name=table[0]
                schema_info_context=f"{schema_info_context}\nTable:{table_name}"


                # Adding Columns and datatype
                cursor.execute("select column_name, data_type from information_schema.columns where table_name=%s;",(table_name,))
                column_list=cursor.fetchall()

                for column in column_list:
                    column_name=column[0]
                    data_type=column[1]
                    schema_info_context=f"{schema_info_context} Column: {column_name}, Data Type:{data_type}\n"

                # Adding Sample data
                cursor.execute(f"select * from {table_name} limit 5;")
                sample_data=cursor.fetchall()
                schema_info_context=f"{schema_info_context} Sample Data:\n"
                for row in sample_data:
                    schema_info_context=f"{schema_info_context} {row}\n"
        except Exception as e:
            print(f"Error fetching schema details: {e}")
            schema_info_context = f"Error fetching schema details: {e}"

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return schema_info_context


    def execute_sql(self,query):
        try:
            connection= self.connection
            cursor=connection.cursor()
            cursor.execute(query)
            result=cursor.fetchall()
            return str(result)
        except Exception as e:
            print(f"Error executing query: {e}")
            return f"Error executing query: {e}"
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()  



    

obj = DatabaseUtil({
    "host": os.environ["host"],
    "port": os.environ["port"],
    "user": os.environ["user"],
    "password": os.environ["password"],
    "dbname": os.environ["database"]
})

result = obj.schema_details("public")

with open("test_schema_details.txt", "w") as f:
    f.write(result)

            

