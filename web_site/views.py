from flask import (Blueprint,
                   flash, 
                   render_template, 
                   request,
                   current_app)
from . import (get_pdf_text,
                    get_text_chunks,
                    get_vectorstore,
                    get_conversation_chain,
                    handle_userinput,
                    load_conversation,

                    db)
import requests
from langchain.schema import AIMessage,HumanMessage
from flask_login import login_required,current_user
from .models import Queries
import os


def load_current_chat():
    chat_history=[]
    chat_=db.session.query(Queries).filter(Queries.user_id==current_user.id).order_by(Queries.date).limit(10)
    for chat in chat_:
        chat_history.append((chat.query,chat.answer))
    return chat_history    



views=Blueprint('views',__name__)


@views.route('/',methods=['GET','POST'])
@login_required
def home():
    chat_history=load_current_chat()    
    if request.method=='POST':         
        user_question=request.form.get('user_q')
        response=requests.post(url='http://127.0.0.1:3000/converse',json={'chat_history':chat_history,'query':user_question}).json()
        if response['chat_history']:
            query,answer=response['question'],response['answer']
            new_query=Queries(query=query,answer=answer,user_id=current_user.id)
            db.session.add(new_query)
            db.session.commit()
            chat_history.append((query,answer))
            print(response['chat_history'])
        else:
            flash("There was some kind of error in  your query!",category='error')
    return render_template('query.html',chat_history=chat_history,user=current_user)

@views.route('/upload',methods=["GET","POST"])
@login_required
def load_docs():
    if not os.path.exists(current_app.config['UPLOAD_DIR']):
        os.makedirs(current_app.config['UPLOAD_DIR'])
    if request.method=='POST':
        files=request.files.getlist('file')
        print(files)
        pdf_docs=[]

        for file in files:
            if os.path.splitext(file.filename)[1] in current_app.config['ALLOWED_EXTENSIONS']:
                doc_dir=os.path.join(current_app.config['UPLOAD_DIR'],file.filename)
                file.save(doc_dir)
                pdf_docs.append(doc_dir)
            else:
                flash(f'File: {file.filename} is not of the required format!',category='error')
        # if file:
        #     if not isinstance(file, list):
        #         file.save(os.path.join(current_app.config['UPLOAD_DIRECTORY'],f'input{os.path.splitext(file.filename)[1]}'))
        response=requests.post(url='http://127.0.0.1:3000/upload',json={'pdf_docs':pdf_docs}).json()
        pdf_docs=response['pdf_docs']
        if pdf_docs:
            for pdf_path in pdf_docs:
                flash(f'File {os.path.split(pdf_path)[1]} uploaded',category='success')
        else:
            flash(f"Files not Uploaded, some error occurred in server",category='error')
    return render_template('uploads.html',user=current_user)

