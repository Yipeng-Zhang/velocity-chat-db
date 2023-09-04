import re
import matplotlib.pyplot as plt
import json

from db_connector import DbConnector
from prompt_generator import PromptGenerator
from path_decision_predictor import PathDecisionPredictor


class QuestionModel:

    def __init__(self):
        db_name_list = ["data"] #db name = file name

        self.db_connector = DbConnector(db_name_list)
        self.prompt_generator = PromptGenerator()
        self.path_decision_predictor = PathDecisionPredictor(self.prompt_generator)
        # self.db_structure_generator = db_structure_generator.db_structure_generator()
        # self.db_structure_generator.set_db_connector(self.db_connector)

    def get_table_schema(self, db_name, table_name):
        table_schema = self.db_connector.get_table_schema(db_name, table_name)
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

    def get_inf_from_table(self, db_name, table_name, question):
        print("-- get table structure")
        table_schema = self.get_table_schema(db_name, table_name)

        print("-- generating sql to answer the question")
        response = self.prompt_generator.generate_sql(table_schema, question)
        sql = self.extract_sql_from_content(response)
        columns = self.extract_column_names(sql)

        while "Error formate!" in sql:
            print("-- Error formate!, regenerate sql")
            response = self.prompt_generator.correct_sql_response_formate(response)
            sql = self.extract_sql_from_content(response)
            
        print("Sql:", sql)
        sql_result = self.db_connector.exe_sql(db_name, sql)
        result_list = [list(row) for row in sql_result]

        # # Serialize the list of lists to JSON
        # self.result_json = json.dumps(result_as_lists, indent = 4)
        
        print("Sql result:", result_list)
        # print(type(result_list))

        while "Error" in sql_result:
            #syntax error
            print("-- SQL syntax error, trying to correct SQL")
            response = self.prompt_generator.correct_sql(table_schema, sql, sql_result)
            sql = self.extract_sql_from_content(response)

            while "Error formate!" in sql:
                #chatgpt sql formate error
                print("---- Error formate!, regenerate sql")
                response = self.prompt_generator.correct_sql_response_formate(response)
                sql = self.extract_sql_from_content(response)

            sql_result = self.db_connector.exe_sql(sql)

        result_list = [list(row) for row in sql_result]
        result_markdown = self.transfer_to_markdown(result_list, columns)
        return result_markdown

    def extract_json_from_response(self, response_raw):
        json_match = re.search(r'{\s*"option":.*?"response":.*?}', response_raw, re.DOTALL)
        if json_match:
            json_string = json_match.group()
            json_data = json.loads(json_string)
            return json_data        
        
    def debug_mode(self, command):
        if "message_list" in command:
            print(self.prompt_generator._display_all_sesion(self.prompt_generator.message_list))

    def answer_question(self, question):
        if "debug" in question:
            self.debug_mode(question)
            return ""
        db_name = "data"
        table_name = "data"


        option, response = self.path_decision_predictor.if_general_confersation(question)
        if option == 1: #general talk
            print("-- general talk")
            return response
        elif option == 2:
            pass
        else:
            print("-- Error option on [if_general_confersation]")
        
        print("-- Start generating answer")
        option, response = self.path_decision_predictor.if_new_confersation(question)
        self.prompt_generator.add_new_message("user", question)
        if option == 1: #continue talk, no data requried
            print("-- answer by previous conversation")
            print("respone 1:", response)
            response = self.prompt_generator.continue_talk()
            print("respone 2:", response)
            self.prompt_generator.add_new_message("assistant", response)
            return response
        elif option == 2: #new talk, data required
            print("-- answer by searching database")
            # self.prompt_generator.reset_message()
            result_markdown = self.get_inf_from_table(db_name, table_name, question)
        else:
            print("-- Error option on [if_new_confersation]")

        option, response = self.path_decision_predictor.if_display_data(question, result_markdown)
        if option == 1: #directly display data
            print("-- display data directly")
            self.prompt_generator.add_new_message("assistant", result_markdown)
            return result_markdown
        elif option == 2:
            print("-- summary conclusion")
            response = self.prompt_generator.get_final_result(question, result_markdown)
            self.prompt_generator.add_new_message("assistant", response)
            return response
        else:
            print("-- Error option on [if_display_data]")

    def transfer_to_markdown(self, result_list, columns):
        if len(columns) != len(result_list[0]):
            print("columns length", len(columns), "result length", len(result_list[0]))
            print(columns)
            print(result_list)
            raise ValueError("Number of columns must match the length of the header list")

        header_row = "|" + " | ".join(columns) + "|"
        separator_row = "|" + " | ".join(["---"] * len(columns)) + "|"
        data_rows = []

        for row in result_list:
            formatted_row = "|" + " | ".join(map(str, row)) + "|"
            data_rows.append(formatted_row)

        # Join all parts to create the Markdown table
        markdown_table = header_row + separator_row + "".join(data_rows)

        return markdown_table

    def extract_column_names(self, sql_query):
        # Find all occurrences of "SELECT" to "FROM" (case-insensitive)
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_query, re.IGNORECASE | re.DOTALL)
        
        if select_match:
            select_clause = select_match.group(1)
            
            # Split the select clause by commas
            columns = re.split(r',', select_clause)
            
            # Extract column names based on "AS" or second comma
            column_names = []
            for column in columns:
                match = re.search(r'AS\s+"([^"]+)"', column, re.IGNORECASE)
                if match:
                    column_names.append(match.group(1))
                else:
                    column_names.append(column.strip())
            
            return column_names
        
        return []


if __name__ == "__main__":
    question_model = QuestionModel()

    # result = [[246, 18.252034857443167, 9.38206314601763, 26.900505216626126, 4, 81, 240, 238, 234, 234, 167, 3, 10, 20, 37, 89, 3, 11, 2, 1, 2, 109]]
    # sql = """SELECT      COUNT(*) AS total_records,     AVG("mean protein (% w/w)") AS avg_protein,     MIN("mean protein (% w/w)") AS min_protein,     MAX("mean protein (% w/w)") AS max_protein,     COUNT(DISTINCT "set number") AS distinct_set_numbers,     COUNT(DISTINCT "plate ID") AS distinct_plate_ids,     COUNT(DISTINCT "line name") AS distinct_line_names,     COUNT(DISTINCT "CAR#") AS distinct_car_numbers,     COUNT(DISTINCT "CLIMA ID") AS distinct_clima_ids,     COUNT(DISTINCT "Accession identifier") AS distinct_accession_identifiers,     COUNT(DISTINCT "Alternate accession identifier") AS distinct_alternate_accession_identifiers,     COUNT(DISTINCT "Biological status") AS distinct_biological_statuses,     COUNT(DISTINCT "REGION") AS distinct_regions,     COUNT(DISTINCT "SUBREGION") AS distinct_subregions,     COUNT(DISTINCT "Country of origin") AS distinct_countries_of_origin,     COUNT(DISTINCT "STATE/PROVINCE") AS distinct_states_provinces,     COUNT(DISTINCT "Basic descriptor") AS distinct_basic_descriptors,     COUNT(DISTINCT "Colour") AS distinct_colours,     COUNT(DISTINCT "Genebank") AS distinct_genebanks,     COUNT(DISTINCT "TAX_NAME") AS distinct_tax_names,     COUNT(DISTINCT "Hemisphere") AS distinct_hemispheres,     COUNT(DISTINCT "SITE") AS distinct_sites FROM      data;"""
    # columns = question_model.extract_column_names(sql)
    # print("columns")
    # print(columns)
    # print("table")
    # print(question_model.transfer_to_markdown(result, columns))
    # exit()



    # question = "what is the top-10 protein value?"
    question = "Show me the top 5 highest sd protein with information that are the most related to protein."
    # question = "Which attribute affects the protein value more, latitude or longitude?"
    # question = "which two subregions have the most different protein value?"
    # question = "If I want to get higher protein, which Hemisphere is better?"
    # response = QuestionModel.answer_question(question)
    while True:
        print("=================================================")
        question = input("User: ")
        print("-------------------------------------------------")
        response = question_model.answer_question(question)
        print("Magda: ")
        if len(response) > 0:
            print(response)
            print("-------------------------------------------------")

