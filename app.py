from web_site import create_app
from web_site import load_conversation
from flask import current_app

app=create_app()

if __name__=="__main__":
    app.run(debug=True,load_dotenv=True,host='localhost',port=4000)
    