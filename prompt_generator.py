import openai
import time


test = True # set True for displaying more detials

is_chatgpt = True

model_version = "vicuna-13b-v1.5"

class PromptGenerator:
    
    def __init__(self):
        with open('/home/zha324/Data/openai_key', 'r') as file:
            key = file.read()
        self.model_version = model_version

        openai.api_key = "EMPTY"
        if not is_chatgpt:
            openai.api_base = "http://localhost:8000/v1"
        self.reset_message()

        if is_chatgpt:
            # self.model_version = "gpt-3.5-turbo"    # gpt-3.5-turbo   gpt-4
            self.model_version = "gpt-4"    # gpt-3.5-turbo   gpt-4
            # print("key", key)
            openai.api_key = key
        
    def call_gpt_api(self, message_list):
        max_retries = 3  # Maximum number of retries
        for _ in range(max_retries):
            try:
                if is_chatgpt:
                    completion = openai.ChatCompletion.create(
                        model = self.model_version,
                        messages = message_list, 
                        temperature = 0.
                    )
                else:
                    completion = openai.ChatCompletion.create(
                        model = self.model_version,
                        messages = message_list
                    )
                return completion.choices[0].message.content
            except Exception as e:
                print(e)
                if "reduce the length" in str(e):
                    self.remove_message(message_list)
                
        # If all retries failed, raise an error or return a default value
        raise Exception("API call failed after multiple retries.")
    
    def continue_talk(self):
        return self.call_gpt_api(self.message_list)

    
    def next_step_single_selection(self, question, options, background):
        prompt = f"""
        Here is the message from the user "{question}"

        {background}

        I need you to select one option that can best discrip user's message from the following options' discriptions.
        Each option is introduces in the from of "[index] option discription."

        {options}

        You can write how you think about this question and give your thought step-by-step.
        Finaly, you can select one option, and you may be asked to response the user's question.
        The option and the possible response should be formed as a Json object.
        For example:
        {{
            "option": 1,
            "response": "response for option 1."
        }}
        """
        message = {"role": "user", "content": prompt}
        self.message_list.append(message)
        response = self.call_gpt_api(self.message_list)
        if test:
            # self._display_information_debug(prompt,response)
            # self._display_all_sesion(self.message_list, "message_list")
            print(response)
        self.message_list.pop() #prompt for selection is not important
        return response
    
    def next_step_mulpitle_selection(self, question, options, background):
        prompt = f"""
        Here is the message from the user "{question}"

        I need you to select at least one option from the following options' discriptions.
        Each option is introduces in the from of "[index] option discription."

        {options}

        You should select at least one option, and provide your response to the user's question.
        The options and possible respones should be formed as a Json object.
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
        message = {"role": "user", "content": prompt}
        self.message_list.append(message)
        response = self.call_gpt_api(self.message_list)
        if test:
            # self._display_information_debug(prompt,response)
            # self._display_all_sesion(self.message_list,"message_list")
            print(response)
        self.message_list.pop() #prompt for selection is not important
        return response


    def generate_sql(self, table_schema, question):
        self.message_list_temp = []
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

        message = {"role": "user", "content": prompt}
        self.message_list_temp.append(message)
        response = self.call_gpt_api(self.message_list_temp)
        message_response = {"role": "assistant", "content": response}
        self.message_list_temp.append(message_response)
        if test:
            # self._display_information_debug(prompt,response)
            self._display_all_sesion(self.message_list_temp, "message_list_temp")
        return response
    

    def get_final_result(self, question, sql_result):
        prompt = f"""
        Running the previous SQL, we get the following data:
        {sql_result}

        First, you should introduce the data.
        For example, "The following data is for answring the question:", then show the data in the markdownn form.
        Second, if any column is not from the table directly, but genereated by multiple columns, you shoulf introduct how we get the data? 
        For what purpose you select these columns?
        For example, "The columns are xxx, xxx, respectively. Column xxx is computed by xxx, etc."
        Tired, if the number of rows is large, you should sumary the data.
        Then, you can answer the question based on the data.
        For example, "According to the data, we conclude that, xxx"
        Last, you can present any insight finds if it is helps answer the question. 
        For example, "There are some insight finds from the data. First, second, etc."
        """

        message = {"role": "user", "content": prompt}
        self.message_list_temp.append(message)
        response = self.call_gpt_api(self.message_list_temp)
        message_response = {"role": "assistant", "content": response}
        self.message_list_temp.append(message_response)
        if test:
            # self._display_information_debug(prompt,response)
            self._display_all_sesion(self.message_list_temp, "message_list_temp")
        return response
    
    def get_columns(self, sql):
        prompt = f"""
        {sql}

        Provide me all columns' names of the above sql as a list.
        For example, [column1, column2, column3].
        Noting that, for a column
        """

        message = {"role": "user", "content": prompt}
        self.message_list_temp.append(message)
        response = self.call_gpt_api(self.message_list_temp)
        message_response = {"role": "assistant", "content": response}
        self.message_list_temp.append(message_response)
        if test:
            # self._display_information_debug(prompt,response)
            self._display_all_sesion(self.message_list_temp, "message_list_temp")
        return response

    
    def _correct_sql(self, table_schema, sql, sql_result):
        prompt = f"""
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

        message = {"role": "user", "content": prompt}
        self.message_list_temp.append(message)
        response = self.call_gpt_api(self.message_list_temp)
        message_response = {"role": "assistant", "content": response}
        self.message_list_temp.append(message_response)
        if test:
            self._display_information_debug(prompt,response)
        return response
    
    def reset_message(self):
        self.message_list = []
        content = "You are a professinal database scienist. You goal is to write SQLs to answer user's question."
        self.add_new_message("system", content)
        # self.messages_general = [{"role": "system", "content": "Given a user's conversation and a list of functions, your tasks is to determinal which tasks are related to user's demand."}]

    def add_new_message(self, role, message):
        self.message_list.append({"role" : role, "content" : message})

    def remove_message(self, message_list):
        message_list.pop(0)

    def get_message_list(self):
        return self.message_list
    
    def _display_information_debug(self, prompt, response):
        print("=================================================")
        print(prompt)
        print("------------------------------------------------")
        print(response)
        print("=================================================")

    def _display_all_sesion(self, message_list, message_list_name):
        print("=================================================")
        print("=============", message_list_name, "==============")
        for item in message_list:
            print("[role]:", item["role"])
            print("[content]:", item["content"])
            print("------------------------------------------------")
        print("=================================================")