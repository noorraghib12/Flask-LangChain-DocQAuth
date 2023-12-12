import regex as re
import os
from google.cloud import translate_v2 as translate
from dotenv import load_dotenv
load_dotenv()
import re
from langchain.chains import RetrievalQAWithSourcesChain
from langchain import OpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.prompts.few_shot import FewShotPromptTemplate
from langchain.prompts.example_selector import SemanticSimilarityExampleSelector
from datetime import datetime,timedelta
from datetime import datetime
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.utils.openai_functions import convert_pydantic_to_openai_function
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain.output_parsers import BooleanOutputParser
from langchain.schema.runnable import RunnableMap,RunnablePassthrough,RunnableLambda
from pydantic import BaseModel,Field,model_validator
from langchain.pydantic_v1 import validator
from langchain.output_parsers import DatetimeOutputParser
from typing import List


os.environ["GOOGLE_APPLICATION_CREDENTIALS"]=r'google_cred.json'
from google.cloud import translate_v2 
translate_model=translate_v2.Client()

embeddings=OpenAIEmbeddings() 
llm = OpenAI(model_name="text-davinci-003")


class eventBoolRetrieve(BaseModel):
    event_truth: bool =Field(description="Validatition of whether the Alleged Event ever truly occured according to the given list of Historical Events")
    event_date: datetime =Field(description= "The date fetched from the retrieved event")
    
    @model_validator(mode='after')
    def vali_date(self):
        if self.event_truth==False:
            self.event_date=None
        return self


event_verify_prompt=PromptTemplate(template="""Each sentence is a specific historical event in the Historical Events. Given the list of historical events, determine if the alleged event ever truly occurred. Answer only in boolean format. If you're not sure, just reply with 'False'.
Historical Events: {retrieved}      

Alleged Event: {queried}
""",
input_variables=['queried','retrieved'],
)
bool_parse=BooleanOutputParser(true_val='True',false_val='False')






def convert2days(string):
    days_dict={'month':30,'week':7,'year':365,'day':1}
    date_pat=re.compile(r'((?P<year>\d* )(?:year|YEAR|years|YEARS|))?(?: and |, | )?((?P<month>\d* )(?:month|MONTH|months|MONTHS))?(?: and |, | )?((?P<week>\d* )(?:week|WEEK|weeks|WEEKS))?(?: and |, | )?((?P<day>\d* )(?:day|DAY|days|DAYS|))')
    regx=re.match(date_pat,string)
    res={key:int(value) for key,value in regx.groupdict().items() if value is not None}
    tot_days=sum([res[key]*days_dict[key] for key in res.keys()])
    return timedelta(days=tot_days)

def get_date(event):
    if event:
        date_str=(event[0].page_content).split(':')[0]
        date_str=date_str.split(" (")[0]
        return_date=datetime.strptime(date_str.strip(),"%B %d, %Y")
        return return_date

    else:
        date_str=None
        return date_str
    


def get_final_date(d_):
    if not d_['event_truth']:
        return "Sorry, this event never occurred, or it is not within our event database"
    if d_['before_after']=='after':
        return (d_['event_date']+d_['delta']).strftime("%B %d, %Y") 
    else:
        return (d_['event_date']-d_['delta']).strftime("%B %d, %Y")




#main base class for fetched event data
class eventDetails(BaseModel):
    ''' Used to extract important information related to an individual's birthday'''
    time_span:str = Field(description="Timespan from the event that occurs before or after the birth of person as mentioned in the query")
    before_after:str =Field(description="Whether the birth of the person in question happened before or after the event")
    event: str = Field(description="Description of the event related to the person's birthday")

    @validator('time_span')
    def span_validate(cls,field):
        return convert2days(field)

#main tagging and extraction function
functions=[
    convert_pydantic_to_openai_function(eventDetails, name='event_details'),
]
# main conversation prompt
prompt=ChatPromptTemplate.from_messages([
    ('system',"You are an assistant to a confectionary store currently working on finding people's birthdays based on certain events that happened before or after them. Refer to 'event_details' function to extract information whenever you are asked about inferring someone's birthdays. Answer conventional questions with conventional replies. Do not make up false information. If you dont know something, simply say you dont know. If you cant find enough context to extract required information from birth date related queries, say that there isnt enough context to infer birthday. In the case you cant get all the required parameters during function calls, say there wasnt enough context."),
    ('user', "{statement}")]
)

json_parser=JsonOutputFunctionsParser()

#chain for extracting birthdays from queries and retrieved documents
vectorstore_dir="./static/vectorstore_db"
db=Chroma(persist_directory=vectorstore_dir,embedding_function=embeddings)


def get_main_chain(db:Chroma=db):
    retriever=db.as_retriever(search_type='similarity_score_threshold',search_kwargs={'score_threshold':0.75, 'k':1})
    model=ChatOpenAI().bind(functions=functions) 
    event_bool_chain= event_verify_prompt | llm | bool_parse
    chain2= json_parser | RunnableMap(
        {
            'retrieved': lambda x: retriever.get_relevant_documents(x['event']),
            "queried": lambda x: x['event'],
            'delta': lambda x: convert2days(x['time_span']),
            'before_after':lambda x:x['before_after']    
        }
    ) | RunnablePassthrough.assign(event_date=lambda x:get_date(x['retrieved'])) | RunnablePassthrough.assign(event_truth=event_bool_chain)| get_final_date



    chain=RunnableMap({'statement':lambda x:translate_model.translate(x,target_language='en')['translatedText']}) | prompt | model | RunnableLambda(lambda x : chain2 if len(x.content)==0 else x.content) 
    return chain

if __name__=="__main__":
    chain=get_main_chain()
    print(chain.invoke("What did you eat today ?"))
    print(chain.invoke("পৌষ ১৯৭৯ এ মেহেরপুরে অনশন শুরু হওয়ার ১ বছর, ২ মাস ১০ দিন আগে জাহিদের জন্ম হয়। সে কখন জন্মগ্রহণ করেছিল ?"))