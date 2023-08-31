from flask import Flask, request, jsonify
from flask_cors import CORS
import sql_reader


app = Flask(__name__)
headers = "http://velocity-ev:6108"
methods = "GET, POST, PUT, DELETE, OPTIONS"
credentials = "Content-Type, Authorization, cache-control,expires,pragma,x-magda-api-key,x-magda-api-key-id"
CORS(app, origins="http://velocity-ev:6108", supports_credentials=True)


@app.route('/sql_question', methods=['POST'])
def question():
    # user_question = request.form.get('user_question')
    user_question = request.data.decode('utf-8') 
    print("user question", user_question)
    answer = sql_reader.sql_reader()

    # response_data = answer.answer_question(user_question)
    # response = jsonify(response_data)
    
    # response.headers['Access-Control-Allow-Origin'] = 'http://velocity-ev:6108'
    # response.headers['access-control-allow-credentials'] = 'true'
    # response.headers['access-control-allow-credentials'] = 'GET, POST, PUT, DELETE, OPTIONS'
    # response.headers['access-control-allow-credentials'] = 'Content-Type, Authorization, cache-control,expires,pragma,x-magda-api-key,x-magda-api-key-id'
    
    return jsonify(answer.answer_question(user_question))

# @app.route('/sql_question', methods=['OPTIONS'])
# def question_option():
#     response = jsonify("")
#     response.headers['Access-Control-Allow-Origin'] = 'http://velocity-ev:6108'
#     response.headers['access-control-allow-credentials'] = 'true'
#     response.headers['access-control-allow-credentials'] = 'GET, POST, PUT, DELETE, OPTIONS'
#     response.headers['access-control-allow-credentials'] = 'Content-Type, Authorization, cache-control,expires,pragma,x-magda-api-key,x-magda-api-key-id'
#     return response 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8067)