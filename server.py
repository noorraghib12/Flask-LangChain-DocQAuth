from dotenv import load_dotenv
load_dotenv()
from flask import (Flask, 
                   request,
                   current_app,
                   jsonify)

# import eventlet
# from eventlet import wsgi
# eventlet.monkey_patch()
from web_site import (get_pdf_text,
                    get_text_chunks,
                    get_vectorstore,
                    get_conversation_chain,
                    handle_userinput,
                    get_chat_history,
                    VECTORSTORE_DIR)
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from dotenv import load_dotenv
from langchain.prompts.chat import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.prompts.prompt import PromptTemplate
from langchain.embeddings import OpenAIEmbeddings
from dotenv import load_dotenv
from langchain.vectorstores import Chroma
import os
from typing import Sequence,Tuple
import asyncio
from server_utils import get_main_chain
# views=Blueprint('views',__name__)


def regex_text_splitter(pdf_path='test_grey (1).pdf', deli_='\n\n'):


    if isinstance(pdf_path,str):

        reader=PdfReader(pdf_path)
        text=""
        for page in reader.pages:
            text+=page.extract_text()
        split_patt=r'((?:January|February|March|April|July|August|September|November|December))'
        
        text=re.sub(split_patt,r'{}\1'.format(deli_),text)
        inp_list=text.split(deli_)

        return [i.strip().replace('\n', r"") for i in inp_list]
    else:

        extended_list=[]
        for pdf in pdf_path:
            extended_list.extend(regex_text_splitter(pdf,deli_=deli_))
    
        return extended_list
    
    
async def handle_userinput(user_question,conversation,chat_history):
    # bot=cache.get('conversation')
    response= conversation.invoke(user_question)
    print(chat_history)
    print(response)
    result={'question':user_question,
            'answer':response,
            'chat_history':chat_history}
    # cache.set('chat_history',response['chat_history'])
    return result






app=Flask(__name__)
app.config['VECTOR_DIR']=VECTORSTORE_DIR
app.config['UPLOAD_DIR']="./static/uploads"
app.config['SECRET_KEY']='abcdefgh'


@app.route('/converse',methods=['POST'])
async def query():
    data=request.get_json()
    query : str = data.get('query')
    chat_history : Sequence[Tuple[str]] = data.get('chat_history')

    # if not chat_history:
    #     chat_history=[("hi","hi")]
    response=await handle_userinput(query,current_app.conversation,chat_history)
        # if len(chat_history)>0:
        #     enum_chat_hist=enumerate(chat_history)

    return jsonify(response)

@app.route('/upload',methods=["GET","POST"])
async def load_docs():
    data=request.get_json()
    pdf_docs: Sequence[str] = data.get('pdf_docs')
    text_chunks = regex_text_splitter(pdf_path=pdf_docs)
    current_app.vectorstore.add_text(text_chunks)
    current_app.conversation = get_main_chain(db=current_app.vectorstore)
    # cache.set('conversation',conversation)
    return jsonify({'pdf_docs':pdf_docs})


    



if __name__=='__main__':

    with app.app_context():
        current_app.vectorstore= get_vectorstore(text_chunks=[],p_dir=app.config['VECTOR_DIR'])
        current_app.conversation= get_main_chain(current_app.vectorstore)
    app.run(port=3000,debug=True)
    # wsgi.server(eventlet.listen(('127.0.0.1',3000)), app)