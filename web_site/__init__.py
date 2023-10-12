from flask import Flask

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings,HuggingFaceInstructEmbeddings
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from dotenv import load_dotenv
from langchain.prompts.prompt import PromptTemplate
from typing import Union,Sequence
import os
load_dotenv()
db=SQLAlchemy()
DB_NAME="database.db"


def create_database(app):
    if not os.path.exists('./website/'+DB_NAME):
        with app.app_context():
            db.create_all()
        print("Created Database!")


VECTORSTORE_DIR="./static/vectorstore_db"

def get_pdf_text(pdf_docs):
    text=""
    for pdf in pdf_docs:
        pdf_reader=PdfReader(pdf)
        for page in pdf_reader.pages:
            text+=page.extract_text()
    return text

def get_text_chunks(text):
    text_splitter= CharacterTextSplitter(
        separator='\n',
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len

    )
    chunks = text_splitter.split_text(text)
    return chunks

def get_vectorstore(text_chunks,p_dir):
    print(text_chunks)
    embeddings=OpenAIEmbeddings() 
    vectorstore=Chroma(persist_directory=p_dir, embedding_function=embeddings)
    vectorstore.add_texts(text_chunks)
    return vectorstore

def get_chat_history(inputs) -> str:
    
    res = []
    for human, ai in inputs:
        res.append(f"Human:{human}\nAI:{ai}")
    return "\n".join(res)



def get_conversation_chain(vectorstore):
    llm=ChatOpenAI()
    custom_template = """Given the following conversation and a question, find further contextual information about the question from your vectorstore and answer accordingly. In case the question is about a date, answer with only the approximate date inferred from the information you have gathered. 
                        Chat History:
                        {chat_history}
                        Question: {question}
                        Answer:"""
    q_template=PromptTemplate.from_template(custom_template)

    conversation_chain=ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        get_chat_history=get_chat_history        
    )
    return conversation_chain

def handle_userinput(user_question,conversation,chat_history):
    # bot=cache.get('conversation')
    bot=conversation
    response=bot({"question": user_question,"chat_history":chat_history})
    # cache.set('chat_history',response['chat_history'])
    return response

    

def load_conversation(db_dir):
    embeddings=OpenAIEmbeddings()
    db=Chroma(persist_directory=db_dir, embedding_function=embeddings)

    return get_conversation_chain(db)

conversation=load_conversation(VECTORSTORE_DIR)
chat_history=[]



def create_app():
    app=Flask(__name__)


    app.config['VECTOR_DIR']=VECTORSTORE_DIR
    app.config['UPLOAD_DIR']="./static/uploads"
    app.config['SECRET_KEY']='abcdefgh'
    app.config['ALLOWED_EXTENSIONS']=['.pdf',]
    app.config['SQLALCHEMY_DATABASE_URI']=f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from .auth import auth
    from .views import views

    app.register_blueprint(auth,url_prefix="/")
    app.register_blueprint(views,url_prefix="/")

    from .models import User,Queries

    create_database(app)
    login_manager=LoginManager()
    login_manager.login_view='auth.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))
    
    return app




