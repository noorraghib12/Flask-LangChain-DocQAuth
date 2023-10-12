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
# views=Blueprint('views',__name__)


def get_conversation_chain(vectorstore):
    llm=ChatOpenAI()
    general_system_template = """ You infer birthdays based on user questions. Use the retrieved context to infer answers to questions at the end.     
    ----
    CONTEXT = {context}
    ----
    """
    general_user_template=""" Here is the next question along with conversation. Try to use your contexts from system along with chat history to provide proper answers. Most of the questions will be about inferring the date of birth for person 'X' given some event that occurred and a timespan between the birth of person 'X' and the occurred event. If the timespan is provided in days within the question, answer with full day, month and year of birth. If it is provided in months, provide answer with month and year of birth only.
    ----
    QUESTION = {question}
    ----
    CHAT HISTORY = {chat_history}
    ----
    """
    messages = [
            SystemMessagePromptTemplate.from_template(general_system_template),
            HumanMessagePromptTemplate.from_template(general_user_template)
            ]
    qa_prompt = ChatPromptTemplate.from_messages( messages )
    conversation_chain=ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        get_chat_history=get_chat_history,        
        combine_docs_chain_kwargs={'prompt': qa_prompt}
    )
    return conversation_chain

async def handle_userinput(user_question,conversation,chat_history):
    # bot=cache.get('conversation')
    response= conversation({"question": user_question,"chat_history":chat_history})
    # cache.set('chat_history',response['chat_history'])
    return response



def load_conversation(db_dir):
    embeddings=OpenAIEmbeddings()
    db=Chroma(persist_directory=db_dir, embedding_function=embeddings)
    return get_conversation_chain(db)




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
    print(pdf_docs)
    raw_text = get_pdf_text(pdf_docs)
    text_chunks = get_text_chunks(raw_text)
    vectorstore = get_vectorstore(text_chunks=text_chunks,p_dir=app.config['VECTOR_DIR'])
    current_app.conversation = get_conversation_chain(vectorstore)
    # cache.set('conversation',conversation)
    return jsonify({'pdf_docs':pdf_docs})


if __name__=='__main__':

    with app.app_context():
        current_app.conversation= load_conversation(app.config['VECTOR_DIR'])
    app.run(port=3000,debug=True)
    # wsgi.server(eventlet.listen(('127.0.0.1',3000)), app)