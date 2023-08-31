import openai
import time


test = False # set True for displaying more detials

is_chatgpt = True

model_version = "vicuna-13b-v1.5"

class prompt_generator:
    
    def __init__(self):
        self.model_version = model_version
        openai.api_key = "EMPTY"
        if not is_chatgpt:
            openai.api_base = "http://localhost:8000/v1"
        self.reset_messages()

        if is_chatgpt:
            # self.model_version = "gpt-3.5-turbo"    # gpt-3.5-turbo   gpt-4
            self.model_version = "gpt-4"    # gpt-3.5-turbo   gpt-4
            openai.api_key = "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"
        
    def reset_messages(self):
        self.messages = [{"role": "system", "content": "You are a professinal database scienist. You goal is to write SQLs to answer user's question."}]
        self.messages_general = [{"role": "system", "content": "Given a user's conversation and a list of functions, your tasks is to determinal which tasks are related to user's demand."}]

    def setDataSchema(self, dataSchema):
        self.dataSchema = dataSchema

    def setQuestion(self, question):
        self.query = question

    def call_gpt_api(self, prompt, message_input):
        max_retries = 10  # Maximum number of retries
        retry_delay = 1  # Delay between retries in seconds

        for _ in range(max_retries):
            try:
                if is_chatgpt:
                    completion = openai.ChatCompletion.create(
                        model = self.model_version,
                        messages = message_input, 
                        temperature = 0.
                    )
                else:
                    completion = openai.ChatCompletion.create(
                        model = self.model_version,
                        messages = message_input
                    )

                print (prompt)
                    
                return completion.choices[0].message.content
            except Exception as e:
                # print("Retrying...")
                if "reduce the length" in str(e):
                    self.messages.pop(0)
                    # print("messages length:", len(self.messages))
                    continue
                # time.sleep(retry_delay)

        # If all retries failed, raise an error or return a default value
        raise Exception("API call failed after multiple retries.")
    
    def next_step_single_selection(self, question, options):

        prompt = f"""
        Here is the message from the user "{question}"

        I need you to select one option from the following options' discriptions.
        Each option is introduces in the from of "[index] option discription."

        {options}

        You can write how you think about this question and give your thought step-by-step.
        Finaly, you can select one option, and provide your response to the user's question.
        The option and responsed should be formed as a Json object.
        For example:
        {{
            "option": 1,
            "response": "response for option 1."
        }}
        """
        message_new = {"role": "user", "content": prompt}
        if len(self.messages_general) == 1:
            self.messages_general.append(message_new)
        else:
            self.messages_general[1] = message_new
        response = self.call_gpt_api(prompt, self.messages_general)
        return response
    
    def next_step_mulpitle_selection(self, question, options):

        prompt = f"""
        Here is the message from the user "{question}"

        I need you to select at least one option from the following options' discriptions.
        Each option is introduces in the from of "[index] option discription."

        {options}

        You should select one option, and provide your response to the user's question.
        The option and responsed should be formed as a Json object.
        Here is the example containing two options
        {{
            {{
                "option": 1,
                "response": "response for option 1."
            }},
            {{
                "option": 2,
                "response": "response for option 2."
            }}
            
        }}
        """
        message_new = {"role": "user", "content": prompt}
        if len(self.messages_general) == 1:
            self.messages_general.append(message_new)
        else:
            self.messages_general[1] = message_new
        response = self.call_gpt_api(prompt, self.messages_general)
        return response


    def task_initialize(self, table_schema, question):

        prompt = f"""
        Given a SQLite table whih the following columns:

        {table_schema}

        The data is related to agricultural or botanical research. 
        The columns cover a wide range of attributes related to plant samples, possibly seeds, and their characteristics.
        Your task is to write a SQL to find data from the above table to answer the question "{question}".

        There are four rules that you need to follow:
        First, you can only use columns provided in the table schema.
        Second, some column names may contain spaces or symbols; you must ensure that the column names remain the same as those shown in the SQLite table schema.
        Third, if a column name contains spaces, it has to be in a pair of double quotes.
        Fourth, the SQL code should be enclosed within [sta] and [end] markers.
        Fifth, the SQL has to be runable in SQLite.

        Here is an SQL example to answer the question "How many recoreds of each type of set number", and your answer should be:
        SQL:
        [sta] select "set number" , count("set number") from data group by "set number"; [end]

        Now, you can start writing the SQL. You can write how you think about this query and give your thought step-by-step.
        For example, you can first analyze which columns in the given tables are related to the query, then think about how to join them.
        """

        message_new = {"role": "user", "content": prompt}
        self.messages.append(message_new)
        response = self.call_gpt_api(prompt, self.messages)
        message_response = {"role": "assistant", "content": response}
        self.messages.append(message_response)

        # print the chat completion
        if test:
            print("=================================================")
            for item in self.messages:
                print("[role]:", item["role"])
                print("[content]:", item["content"])
                print("------------------------")
            print("=================================================")
            input()

        return response
    

    def get_final_result(self, question, sql_result):
        prompt = f"""
        Running the previous SQL, we get the following data:
        {sql_result}

        First, you should introduce the data.
        For example, "The following data is related to the question:", then show the data row by row.
        Second, if any column is not from the table directly, but genereated by multiple columns, you shoulf introduct how we get the data? 
        For what purpose you select these columns?
        For example, "The columns are xxx, xxx, respectively. Column xxx is computed by xxx, etc."
        Tired, if the number of rows is large, you should sumary the data.
        Then, you can answer the question based on the data.
        For example, "According to the data, we conclude that, xxx"
        Last, you can present any insight finds if it is helps answer the question. 
        For example, "There are some insight finds from the data. First, second, etc."
        """

        message_new = {"role": "user", "content": prompt}
        self.messages.append(message_new)
        response = self.call_gpt_api(prompt, self.messages)
        message_response = {"role": "assistant", "content": response}
        self.messages.append(message_response)

        # print the chat completion
        if test:
            print("=================================================")
            for item in self.messages:
                print("[role]:", item["role"])
                print("[content]:", item["content"])
                print("------------------------")
            print("=================================================")
            input()

        return response
    


















    def correct_sql_response_formate(self, sql):
        prompt =f"""
        The SQLite Sql ({sql}) you provided before is not followed the rule.
        The SQL has to start with [sta] and end with [end].
        For example, [sta] select "set number" , count("set number") from data group by "set number"; [end]
        Please providing the SQL only, and no other content
        """

        return self.call_gpt_api(prompt)

    
    def correct_sql(self, table_schema, sql, sql_result):
        pormpt = f"""
        Here is a SQL for SQLite datablase: {sql}

        When run this SQL in SQLite, we get an error:
        {sql_result}

        Following is a SQLite table schema:
        {table_schema}

        Can you correct the above SQL based on four rules:
        First, you can only use columns provided in the table schema.
        Second, some column names may contain spaces or symbols; you must ensure that the column names remain the same as those shown in the SQLite table schema.
        Third, if a column name contains spaces, it has to be in a pair of double quotes. E.g., "mean protein (% w/w)"
        Fourth, please provide SQL output only. The SQL code should be enclosed within [sta] and [end] markers.
        """

        return self.call_gpt_api(pormpt)
    

    def get_figure(self, question, sql_result):
        self.reset_messages()
        pormpt = f"""
        Now, for our question: {question}

        We have the following data {sql_result}

        As I'm using Python, and havd"import matplotlib.pyplot as plt", can you provide Python code to draw a figure to present the data?
        If you do not think this data should be visulized, simply response "print("No figure")".
        Otherwise, you can present the Python code to present this data based on our question.
        Noting that, your response should include the Python code only, but no any other information.
        """

        return self.call_gpt_api(pormpt)
    
    def extract_figure_code(self, code):
        self.reset_messages()
        pormpt = f"""
        Here is the python code you provided me before.

        {code}

        Can you extract the code only for me?
        Do not say another thind in the feed back, but the code only.
        """

        return self.call_gpt_api(pormpt)
