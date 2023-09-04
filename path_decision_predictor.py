import re
import json

class PathDecisionPredictor:

    def __init__(self, prompt_generator):
        self.prompt_generator = prompt_generator

    def if_general_confersation(self, question):
        background = """
        We have a dataset contains quantified proximal composition data from 240 varieties of chickpeas, encompassing information such as their origin, protein, fibre, starch, soluble sugar, and lipid content.
        Your goal is to predict the theme of user's question. If it is the casual conversition, you need to write a response.
        """
        options = """
        [1.] Casual Conversation: This is a casual conversation. The LLM model should respond in a direct and simple manner.
        If you select this option, you should provide a response.
        [2.] Chickpea Dataset Inquiry: This question pertains to the chickpea dataset, which includes sample data on variables like protein content, growth area, location, and more. 
        The answer to this question should involve selecting relevant data from the chickpea dataset.
        If you select this option, you can simply provide "null" as the response.  
        """
        response_raw = self.prompt_generator.next_step_single_selection(question, options, background)
        option, answer = self.extract_json_from_response(response_raw)
        return option, answer
        
    def if_new_confersation(self, question):
        background = """
        Your goal is to predict if this question can be answered based on the prevous conversation.
        """
        options = """
        [1.] Continuation from Previous Conversation: This question can be answered using information from our previous conversation.
        If you select this option, you can directly use the information from the previous conversation to response this question.
        [2.] Fresh Inquiry Requiring Dataset: This question is entirely new and cannot be addressed using previous information. It necessitates fresh data from our dataset.
        If you select this option, you can simply provide "null" as response
        """
        response_raw = self.prompt_generator.next_step_single_selection(question, options, background)
        option, answer = self.extract_json_from_response(response_raw)
        return option, answer
        
    def if_display_data(self, question, data):
        background = f"""
        This is the data we have based on user's message:
        {data}
        """
        options = """
        [1.] Direct Data Display: This question is straightforward, requesting a display of the data. 
        As we already have related data, presenting the data itself suffices; there's no need for additional data summarization to answer the question.
        If you select this option, you can simply provide "null" as response
        [2.] Data-Dependent Inquiry: This question cannot be answered solely by the data itself. The data serves as an information source for addressing the question. 
        We must analyze the data and provide a summarized response based on that analysis to answer the question.
        If you select this option, you can simply provide "null" as response
        """
        response_raw = self.prompt_generator.next_step_single_selection(question, options, background)
        option, answer = self.extract_json_from_response(response_raw)
        return option, answer
    
    def add_message(self, message):
        self.prompt_generator.add_new_message(message)
        
    def extract_json_from_response(self, response_raw):
        try:
            json_match = re.search(r'{\s*"option":.*?"response":.*?}', response_raw, re.DOTALL)
            if json_match:
                json_string = json_match.group()
                json_data = json.loads(json_string)
                return json_data["option"], json_data["response"]
        except Exception as e:
            print("extract_json_from_response Error")
            print("Error:", e)
            print("Response:", response_raw)
