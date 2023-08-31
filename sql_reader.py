import db_connector
import prompt_generator
import db_structure_generator
import re
import matplotlib.pyplot as plt
import json


class sql_reader:

    def __init__(self):
        db_name = "data"

        self.db_connector = db_connector.db_connector(db_name)
        self.prompt_generator = prompt_generator.prompt_generator()
        self.db_structure_generator = db_structure_generator.db_structure_generator()
        self.db_structure_generator.set_db_connector(self.db_connector)

    def get_table_schema(self, table_name):
        table_schema = self.db_connector.get_table_schema(table_name)
        table_schema = bytes(str(table_schema), "utf-8").decode("unicode_escape")
        return table_schema
    
    def extract_answer_from_content(self, content):
        content = content.replace("\n", " ")
        pattern = r"\[sta\](.*?)\[end\]"
        match = re.search(pattern, content)
        if match:
            response_llm = match.group(1).strip()
            return response_llm
        else:
            return "Error formate!"
    
    def extract_sql_from_content(self, content):
        content = content.replace("\n", " ")
        pattern = r"\[sta\](.*?)\[end\]"
        match = re.search(pattern, content)
        if match:
            sql_gpt = match.group(1).strip()
            sql_gpt = bytes(sql_gpt, "utf-8").decode("unicode_escape")
            return sql_gpt
        else:
            pattern = r"```sql(.*?)```"
            match = re.search(pattern, content)
            if match:
                sql_gpt = match.group(1).strip()
                sql_gpt = bytes(sql_gpt, "utf-8").decode("unicode_escape")
                return sql_gpt
            else:
                message_error = "Error formate! Wrong response formate. The SQL is not contained by [sta] and [end]"
                print(message_error)
                print(content)
                print("Tring to extrat from 'SQL: ...... [end]'")
                return message_error

    def get_inf_from_table(self, table_name, question):
        # print("-- get table structure")
        table_schema = self.get_table_schema(table_name)

        # print("-- get table structure")
        # self.db_structure_generator.table_structure_extractor(table_schema)
        # table_structure = self.db_structure_generator.get_table_structure(table_name)
        # print(table_structure)

        # print("-- get sql to answer the question")
        response = self.prompt_generator.task_initialize(table_schema, question)
        sql = self.extract_sql_from_content(response)

        while "Error formate!" in sql:
            print("-- Error formate!, regenerate sql")
            response = self.prompt_generator.correct_sql_response_formate(response)
            sql = self.extract_sql_from_content(response)
            
        print("Sql:", sql)
        self.sql_result = self.db_connector.exe_sql(sql)
        result_as_lists = [list(row) for row in self.sql_result]

        # Serialize the list of lists to JSON
        self.result_json = json.dumps(result_as_lists, indent = 4)

        while "Error" in self.sql_result:
            #syntax error
            print("-- SQL syntax error, trying to correct SQL")
            response = self.prompt_generator.correct_sql(table_schema, sql, self.sql_result)
            sql = self.extract_sql_from_content(response)

            while "Error formate!" in sql:
                #chatgpt sql formate error
                print("---- Error formate!, regenerate sql")
                response = self.prompt_generator.correct_sql_response_formate(response)
                sql = self.extract_sql_from_content(response)

            self.sql_result = self.db_connector.exe_sql(sql)

    def extract_json_from_response(self, response_raw):
        json_match = re.search(r'{\s*"option":.*?"response":.*?}', response_raw, re.DOTALL)
        if json_match:
            json_string = json_match.group()
            json_data = json.loads(json_string)
            return json_data

    def is_general_confersation(self, question):
        options = """
        1. This is a daily conversation. The response can be generated by LLM directly.
        2. This message is highly related to the chickpea dataset whilch contains the sample data such as protein, grown area, location, etc. 
        This question should be answer by selecting data from the chickpea dataset."""
        response_raw = self.prompt_generator.next_step_single_selection(question, options)
        try:
            json_data = self.extract_json_from_response(response_raw)
            if json_data["option"] == 1:
                self.answer = json_data["response"]
                return True
            elif json_data["option"] == 2:
                return False
        except Exception as e:
            print(e)
            print(response_raw)
            return True

            
    def is_final_conclusion(self, question):
        # print("-- get answer")
        options = """
        1. This is a simple question. We already get the data related to this question. Directly showing data is engouh to answer this question.
        2. This is a complex question. Based on the data related to this question, we need to further analyse the data."""

        response_raw = self.prompt_generator.next_step_single_selection(question, options)
        try:
            json_data = self.extract_json_from_response(response_raw)
            if json_data["option"] == 1:
                return False
            elif json_data["option"] == 2:
                return True
        except Exception as e:
            print(e)
            print(response_raw)
            return False
        

    def answer_question(self, question):
        self.answer = ""
        self.files = []
        self.result_json = {}
        
        if not self.is_general_confersation(question):
            table_name = "data"
            self.get_inf_from_table(table_name, question)
            if self.is_final_conclusion(question):
                self.answer = self.prompt_generator.get_final_result(question, [list(row) for row in self.sql_result])

        response = {}
        response["answer"] = self.answer
        response["data"] = self.result_json
        response["files"] = self.files
        return response



        




if __name__ == "__main__":
    sql_reader = sql_reader()
    # question = "what is the top-10 protein value?"
    question = "Show me the top 5 highest sd protein with information that are the most related to protein."
    # question = "Which attribute affects the protein value more, latitude or longitude?"
    # question = "which two subregions have the most different protein value?"
    # question = "If I want to get higher protein, which Hemisphere is better?"
    while True:
        print("=================================================")
        question = input("User: ")
        print("-------------------------------------------------")
        response = sql_reader.answer_question(question)
        print("Magda: ")
        if len(response["answer"]) > 0:
            print(response["answer"])
            print("-------------------------------------------------")

        # if len(response["data"]) > 0:
        #     print(response["data"])
        #     print("------------------------")

        # if len(response["files"]) > 0:
        #     print(response["files"])
        #     print("------------------------")
