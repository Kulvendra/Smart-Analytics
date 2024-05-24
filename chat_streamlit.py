import streamlit as st
import psycopg2
import openai
import openpyxl
import json
import pandas as pd
openai.api_key = "your-open-ai-key"

class PostgresDB:
    def __init__(self, host, database, user, password):
        # Initialize connection parameters
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.connection = None
        self.cursor = None
        self.connect()

    def connect(self):
        try:
            # Establish the connection
            self.connection = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            # Create a cursor object
            self.cursor = self.connection.cursor()
            # print("Connection to PostgreSQL database established successfully.")
        except Exception as e:
            print(f"Error connecting to PostgreSQL database: {e}")

    def execute_query(self, query):
        if self.cursor is None:
            print("Database connection is not established.")
            return None
        try:
            # Execute the SQL query
            self.cursor.execute(query)
            # Fetch and return all results
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Error executing query: {e}")
            return None

    def list_tables(self):
        query = """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
            AND table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY table_schema, table_name;
        """
        result = self.execute_query(query)
        if result:
            return result
        else:
            return "No tables found in the database."
    

    def get_table_schema_and_indices(self, table_name):
        schema_query = f"""
            SELECT
                column_name,
                data_type,
                character_maximum_length,
                numeric_precision,
                is_nullable,
                column_default
            FROM
                information_schema.columns
            WHERE
                table_name = '{table_name}'
            ORDER BY
                ordinal_position;
        """
        indices_query = f"""
            SELECT
                indexname,
                indexdef
            FROM
                pg_indexes
            WHERE
                tablename = '{table_name}';
        """
        constraints_query = f"""
            SELECT
                tc.constraint_name, tc.constraint_type, kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                LEFT JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
            WHERE tc.table_name = '{table_name}';
        """

        schema_result = self.execute_query(schema_query)
        indices_result = self.execute_query(indices_query)
        constraints_result = self.execute_query(constraints_query)

        schema_info = "Column Name | Data Type | Char Max Length | Numeric Precision | Is Nullable | Default Value\n"
        schema_info += "-"*90 + "\n"
        schema_info += "\n".join(
            [f"{row[0]} | {row[1]} | {row[2] if row[2] else ''} | {row[3] if row[3] else ''} | {row[4]} | {row[5] if row[5] else ''}" for row in schema_result]
        ) if schema_result else f"No schema found for table {table_name}"

        indices_info = "\n".join(
            [f"{row[0]}: {row[1]}" for row in indices_result]
        ) if indices_result else f"No indices found for table {table_name}"

        constraints_info = "\n".join(
            [f"{row[0]} ({row[1]}): Column - {row[2]}{(f', References {row[3]}({row[4]})' if row[1] == 'FOREIGN KEY' else '')}" for row in constraints_result]
        ) if constraints_result else f"No constraints found for table {table_name}"

        return f"Schema of table {table_name}:\n{schema_info}\n\nIndices:\n{indices_info}\n\nConstraints:\n{constraints_info}"

    def generate_schema_for_all_tables(self, output_file):
        tables_query = """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
            AND table_schema NOT IN ('information_schema', 'pg_catalog')
            ORDER BY table_schema, table_name;
        """
        tables_result = self.execute_query(tables_query)
        
        if tables_result:
            with open(output_file, 'w') as file:
                for schema, table in tables_result:
                    schema_indices_constraints = self.get_table_schema_and_indices(table)
                    file.write(schema_indices_constraints)
                    file.write("\n\n" + "="*100 + "\n\n")
            print(f"Schema for all tables has been written to {output_file}")
        else:
            print("No tables found in the database.")

    def run_custom_query(self, query):
        print("Executing SQL Query...")
        if self.cursor is None:
            print("Database connection is not established.")
            return None, None
        try:
            # Execute the SQL query
            self.cursor.execute(query)
            # Fetch all results
            data = self.cursor.fetchall()
            # Get column names from cursor description
            headers = [desc[0] for desc in self.cursor.description]
            return data, headers
        except Exception as e:
            print(f"Error executing query: {e}")
            return None, None
        

    def save_to_excel(self, data, headers, file_path):
        try:
            # Create a pandas DataFrame from the data and headers
            df = pd.DataFrame(data, columns=headers)
            # Save the DataFrame to an Excel file
            df.to_excel(file_path, index=False)
            print(f"Data has been written to {file_path}")
        except Exception as e:
            print(f"Error saving to Excel: {e}")

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("PostgreSQL connection closed.")

# ---------------------------End of PostgresDB Class-------------------------------------       




def render_all_echarts(all_configs):


    # Start of the HTML document
    echarts_html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://cdn.jsdelivr.net/npm/echarts/dist/echarts.min.js"></script>
        <style>
            .echart-container { width: 600px; height: 400px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
    """

    # Generate a chart container and JavaScript for each chart in the list
    for chart_title, config in all_configs.items():
        echarts_html_template += f'<div id="{chart_title.replace(" ", "_")}" class="echart-container"></div>\n'
        echarts_html_template += f"""
        <script type="text/javascript">
            var myChart_{chart_title.replace(" ", "_")} = echarts.init(document.getElementById('{chart_title.replace(" ", "_")}'));
            var option = {json.dumps(config)};
            myChart_{chart_title.replace(" ", "_")}.setOption(option);
        </script>
        """

    # End of the HTML document
    echarts_html_template += "</body></html>"

    with open("chartView.html", 'w') as file:
        file.write(echarts_html_template)
    
    return echarts_html_template

def read_text_file(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        return content
    except Exception as e:
            print(f"Error reading file: {e}")
            return None

def getRequiredDbTables(all_tables ,query):
    
    print("Generating SQL Query...")

    prompt = f"You are an expert in database management. You understand the database design and know how to write efficient and accurate SQL queries. I want you to give me list of database table you need to write an efficient and accurate SQL query for a given natural language query based on the given database schema , just make table name should match exactly in the below given list. {all_tables}"

    prompt2 = '''
    return a json in this format => 
    {
        "data":[table1,table4]
    }
    '''

    prompt = prompt + prompt2


    query_prompt = [{"role": "system", "content": prompt}, {"role": "user","content":query}]
  
    response = openai.chat.completions.create(
    model="gpt-4o",
    response_format={ "type": "json_object" },
    messages= query_prompt,
    temperature=0,  # Adjust the temperature for randomness
    top_p=0.1
    )
    data = response.choices[0].message.content
    print("Required List of tables generated..!!")

    return json.loads(data)

def generateData(schema_file,query,schema_str=-1):
    
    print("Generating SQL Query...")

    user_prompt = '''You are an expert in ELM (Enterprise Legal Management) database. 
    You understand the database design and know how to write efficient and accurate SQL queries. 
    For a given user query and database schema, i want you to do the following.

    Step 1: Identify the tables that are needed to answer user query. Use comment of each table to understand if that table is needed or not. Sometimes you may need multi association tables. For example, there is invoiceheaders_lineitems table to map lineitems related to each invoice. There is detaillineitems in invoice but it is an array and it is difficult to use array to join with id in another table. So, you should consider using multi association tables in such cases.
    Step 2: Always use totalamount column when considering invoice related amount/fee instead of totalgrossfeeamount or grossamount or any other column.
    Step 3: Use join only on the same type of column types. For example do not join integer colum with integer array column. In the same way, do not join integer column with text column.
    Step 4: Make sure to use matternarrative also when asked about facts or issues of a specific matter. But use left or right join because sometimes matter narrative may not be present for few matters.
    Step 5: Do not assume or hallucinate. Do not use any tables or columns that are not present in given database schema.
    Step 6: When asked for expected fees, amount or budget always give minimum, average and maximum. Round up the such column values to maximum 2 digits after decimal.
    Step 7: Select only columns that are useful. For example, names are more useful to the end user compared to id columns.
    Step 8: Convert selected column names using alias to meaningful readable names. For example, Total Amount is meaningful name for totalamount column. Use space instead of underscores in alias names and use proper capitalization. Surround the alias names in double quotes to avoid SQL error.
    Step 9: There is no table called matterbudget. In order to understand matter budget, you should look at allocation to understand how much is allocated to an inovoice related to the matter and then look at how much actually spent on the matter.
    Step 10: Avoid using subquery logic. Instead use JOIN
    Step 11: Use the following respective tables to join 2 tables. Key is the table to be used for the respective tables in values. As per below information, you should use matter_matternarrative to join matter, matternarrative tables. When using matter_matternarrative table, you have to carefull check it's fields/columns so that you are joining correctly.
    {
        invoiceheaders_lineitems : invoiceheaders, lineitems
        invoiceheaders_invoiceallocation: invoiceheaders, invoiceallocation
        matter_matterevent: matter, matterevent
        matter_matternarrative: matter, matternarrative
        matter_organization: matter, organization
        person_matter: person, matter
    }
    Step 12: Give maximum of 100 rows.
    Step 13: Based on the tables identified in Step 1 and rules from Step 2-12, write an accurate SQL query to answer user question. Give final response in given JSON format.

    ###Output JSON format:###
    {
        "query":"Select * FROM ......"
    }
    ''' 
    if schema_str!=-1:
        prompt = user_prompt + "\n###Database Schema###\n" + schema_str 
    else:
        file_content = read_text_file(schema_file)
        if file_content is not None:
            # print(file_content)
            prompt = user_prompt + "\n###Database Schema###\n" + file_content 
        else:
            print("Schema not found")
            exit()


    query_prompt = [{"role": "system", "content": prompt}, {"role": "user","content":query}]
  
    response = openai.chat.completions.create(
    model="gpt-4o",
    response_format={ "type": "json_object" },
    messages= query_prompt,
    # max_tokens=50,
    temperature=0,  # Adjust the temperature for randomness
    top_p=0.1
    )
    data = response.choices[0].message.content
    print("SQL query generated..!!")
    print(data)
    return json.loads(data)

def generateEchart(query,data):
    
    print("Generating Echart Config...")

    prompt = '''You generate relevant list of echart config json with given data and query.So that user can copy paste the echart config on its website and plot chart directly and  return json object like => 
    {
        "chartList":{"chartTitle1":config}
    }
    '''
  

    query_prompt = [{"role": "system", "content": prompt}, {"role": "user","content":data}]
  
    response = openai.chat.completions.create(
    model="gpt-4o",
    response_format={ "type": "json_object" },
    messages= query_prompt,
    temperature=0,  # Adjust the temperature for randomness
    top_p=0.1
    )
    data = response.choices[0].message.content
    print("Echart generated..!!")
    # print(data)
    return json.loads(data)

def getResponseType(query,db_data):
        
    print("Analyzing Response type...")

    prompt = '''You will decide best way to response to user query between text,chart and data as response bases on the user query and given data
                if user wants to display chart then return me below json
                {
                "display_type":"chart"
                }
                else if user want data to display 
                {
                "display_type":"data"
                }
                else if user want just text to display 
                {
                "display_type":"text"
                }
        '''

    user_prompt = query + "\n data => \n" + db_data
    query_prompt = [{"role": "system", "content": prompt}, {"role": "user","content":user_prompt}]
  
    response = openai.chat.completions.create(
    model="gpt-4o",
    response_format={ "type": "json_object" },
    messages= query_prompt
    )
    data = response.choices[0].message.content
    print("Response type generated..!!")
    print(data)
    return json.loads(data)

def getTextResponse(query,data):
        
    print("Analyzing Response type...")

    prompt = '''Answer the user query based on the given data'''
    user_prompt = query + " Data => " + data
    query_prompt = [{"role": "system", "content": prompt}, {"role": "user","content":user_prompt}]
  
    response = openai.chat.completions.create(
    model="gpt-4o",
    # response_format={ "type": "json_object" },
    stream=True,
    messages= query_prompt
    )
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="")
            yield chunk.choices[0].delta.content
    # data = response.choices[0].message.content
    # print("Response type generated..!!")
    # # print(data)
    # return json.loads(data)

def getTextWithDataResponse(query,data):
        
    print("Analyzing Response type...")

    prompt = '''Answer the user query based on the given data with proper indepth explantion over the data and it should be an relevant answer to the user question and convert below data into an markdown table with relevant title at end of explanation, just make u converted all the below data into table and not data left'''
    user_prompt = query + " Data => " + data
    query_prompt = [{"role": "system", "content": prompt}, {"role": "user","content":user_prompt}]
  
    response = openai.chat.completions.create(
    model="gpt-4o",
    stream=True,
    # response_format={ "type": "json_object" },
    messages= query_prompt
    )

    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="")
            yield chunk.choices[0].delta.content
    # data = response.choices[0].message.content
    # print("Response type generated..!!")
    # print(data)
    # return json.loads(data)

def convert_to_html_table(headers, data,info):
    # Create the table header with white text color
    html_table = f"<p style=\"color: white;\">{info}</p>"
    html_table += '<table border="1" style="width:100%; border-collapse: collapse;">\n'
    html_table += '  <thead>\n    <tr style="background-color: #333; color: white;">\n'
    for header in headers:
        html_table += f'      <th style="padding: 8px;">{header}</th>\n'
    html_table += '    </tr>\n  </thead>\n'

    # Create the table body with white text color
    html_table += '  <tbody>\n'
    for row in data:
        html_table += '    <tr>\n'
        for cell in row:
            html_table += f'      <td style="padding: 8px; color: white;">{cell}</td>\n'
        html_table += '    </tr>\n'
    html_table += '  </tbody>\n</table>'

    return html_table


def convert_to_markdown_table(headers, data, info):
    # Create the table header with additional info
    markdown_table = f"{info}\n\n"
    
    # Create the table headers
    header_row = " | ".join(headers)
    separator_row = " | ".join(['---' for _ in headers])
    markdown_table += f"{header_row}\n{separator_row}\n"
    
    # Create the table body
    for row in data:
        row_data = " | ".join(str(cell) for cell in row)
        markdown_table += f"{row_data}\n"
    
    return markdown_table
# Function to handle chat interactions
def handle_chat(query):

    output={}
    with open('config.json', 'r') as file:
        config = json.load(file)
    db = PostgresDB(host=config["host"], database=config["database"], user=config["user"], password=config["password"])
    # query = "Provide a range of expected legal fees for specific matter types"
    # db.generate_schema_for_all_tables("database_schema.txt")
    data =generateData("database_schema.txt",query)
    res_type = ""
    if(data['query']): # condition when reponse type is a table data
        custom_query =data['query']
        data, headers = db.run_custom_query(custom_query)
        if data is not None and headers is not None:
            data_str = "Header =>"+ str(headers) + "\n" + "Data =>"+ str(data)
            print(data_str)
            res_output = getResponseType(query,data_str)
            res_type = res_output["display_type"]
        else:
            output["data"] = "Oops Something went wrong while fetching data"  
            output["res_type"] = "text"

    else:
        output["data"] = "Oops Something went wrong while fetching data"  
        output["res_type"] = "text"

    

    if res_type == "data":
        data_str = "Header =>"+ str(headers) + "\n" + "Data =>"+ str(data)
        # text_resv=getTextWithDataResponse(query,data_str)
        output["data"] = {"query":query,"data":data_str}
        # output["data"] = text_resv["data"].replace('$', '\$') 
        # output["data"] = convert_to_markdown_table(headers,data,text_resv["data"].replace('$', '\$')) # convert_to_html_table(headers,data,text_resv['data'])
        output["res_type"] = "data"
     

    elif res_type == "text": # condition when reponse type is a text
        data_str = "Header =>"+ str(headers) + "\n" + "Data =>"+ str(data)
        # text_resv=getTextResponse(query,data_str)
        # output["data"] = text_resv['data']
        output["data"] = {"query":query,"data":data_str}
        output["res_type"] = "text"
       

    elif res_type == "chart": # condition when reponse type is a chart

        data_str = "Header =>"+ str(headers) + "\n" + "Data =>"+ str(data)
        echart_list = generateEchart(query,data_str)
        html_content = render_all_echarts(echart_list['chartList'])
        output["data"] = html_content
        output["res_type"] = "chart"
    
    return output
 
            
       


        


# Streamlit UI setup
st.title("Smart Chatbot")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display chat history using st.chat_message
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        # print(message["content"])
        if message["role"] == "bot" and message['res_type']== "chart" :
            st.components.v1.html(message["content"], height=500, scrolling=True)
        else:
            st.markdown(message["content"])

# User input with st.chat_input
user_input = st.chat_input("You:")

if user_input:
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    

    response_placeholder = st.empty()
    # Generate response from the bot
    response = handle_chat(user_input)


    # full_response = ""
    # for text in get_response(query):
    #     full_response += text
    #     response_placeholder.markdown(full_response)

    if response["res_type"]=="chart":
        # response = handle_chat(user_input)
        st.session_state.chat_history.append({"role": "bot", "content": response['data'],"res_type":response['res_type']})
    elif response["res_type"]=="data":
        st.session_state.chat_history.append({"role": "bot", "content": "","res_type":"data"})
        query = response["data"]['query']
        data = response["data"]['data']
        # output["data"] = text_resv["data"].replace('$', '\$') 
        full_response = ""

        for obj in getTextWithDataResponse(query,data):
            full_response += obj.replace('$', '\$') 
            response_placeholder.markdown(full_response)
        st.session_state.chat_history[-1]["content"] = full_response

    elif response["res_type"]=="text":
        st.session_state.chat_history.append({"role": "bot", "content": "","res_type":"text"})

        query = response["data"]['query']
        data = response["data"]['data']
        # output["data"] = text_resv["data"].replace('$', '\$') 
        full_response = ""
        for obj in getTextResponse(query,data):
            full_response += obj.replace('$', '\$') 
            response_placeholder.markdown(full_response)
        st.session_state.chat_history[-1]["content"] = full_response
    
   
    # Re-render chat history with new messages
    st.rerun()
