# Flask-LangChain-DocQAuth

A bit more scaled up version of my streamlit docQA chatbot. 

**Whats New?**
- Seperate APIs for User Reg/Auth and LLM Query/VectorDB Updating.
- User model based chat history storage and retrieval.

**What's Next?** 
- Hoping to decouple the chains and delve further into stateless deployment schemes for LLM chatbots.
- Hoping to deploy a more robust version of this in Django, with OAuth, JWT authentications for LLM inference API.
- Hoping to find ways to serialize langchain models so as to make them cache-able for backends.
