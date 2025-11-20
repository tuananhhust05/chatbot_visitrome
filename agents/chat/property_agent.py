





import os
from langchain_groq import ChatGroq
from typing import Union, Optional

import weaviate
from langchain.vectorstores import Weaviate

from sentence_transformers import SentenceTransformer

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage



from agents.langchain_integrations.weaviate_retriever import STretriever
from agents.langgraph_propertyagent.build import workflow


from langgraph.types import StateSnapshot
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver


from datetime import datetime
import pytz
# Xác định múi giờ GMT+8
timezone = pytz.timezone('Asia/Singapore')

def print_message_history(snapshot: StateSnapshot):
    print("==================================================")
    for message in snapshot.values['messages']:
        print(message.content)
        print("\n\n==================================================")


def chat(graph: StateGraph, input: str, config: dict):
    inputs = {
        "messages": [
            HumanMessage(content=input)
        ]
    }
    response = dict(list(graph.stream(inputs, config=config))[-1])
    return response


class graph:

    def __init__(
            self,
            llm_model: str = "llama-3.3-70b-versatile",
            # llm_model: str = "llama-3.1-8b-instant",
            # llm_model: str = "gemma2-9b-it",
            # weaviate_url: str = "http://localhost:8080",
            weaviate_url: str = "http://weaviate:8080",
            embedding_model: str = 'all-distilroberta-v1',
            k: int = 5
        ):
    
        self.k = k
        self.embedding = SentenceTransformer(embedding_model)
        client = weaviate.Client(
            url=weaviate_url  # Default local Weaviate URL
        )
        # Create vectorstores for multiple classes
        self.weaviate_vectorstore_support = Weaviate(
            client=client, 
            index_name="SupportAgent", 
            text_key="content",  
            attributes=["category", "content", "url", "doc_id", "chunk_id","agentId"]
        )
        self.weaviate_vectorstore_hotels = Weaviate(
            client=client, 
            index_name="Hotels", 
            text_key="content",  
            attributes=["category", "content", "url", "doc_id", "chunk_id","agentId"]
        )
        self.weaviate_vectorstore_tours = Weaviate(
            client=client, 
            index_name="Tours", 
            text_key="content",  
            attributes=["category", "content", "url", "doc_id", "chunk_id","agentId"]
        )
        # Initialize the agent
        self.agent_chat = ChatGroq(
            model=llm_model, 
            temperature=0,
            api_key=os.getenv("GROQ_API_KEY")
        )
        self.graph=None


    async def intialize_graph(
            self,
            checkpointer: Optional[Union[MemorySaver, PostgresSaver]] = None
        ):
        retriever = STretriever(
            vectorstore_support=self.weaviate_vectorstore_support,
            vectorstore_hotels=self.weaviate_vectorstore_hotels,
            vectorstore_tours=self.weaviate_vectorstore_tours,
            embedding_model=self.embedding, 
            k=self.k
        )
        workflow_ = workflow(retriever=retriever, llm_model=self.agent_chat)
        self.graph = await workflow_.initialize_graph(checkpointer=checkpointer)
        return self.graph
    

    async def chat_calendar(self, input: str, config: dict):
        if not self.graph:
            raise ValueError("Graph not initialized. Call initialize_graph first.")
        # Lấy thời gian hiện tại ở múi giờ GMT+8
        current_time = datetime.now(timezone)

        # Lấy các thông tin: thứ, giờ, phút, ngày, tháng, năm
        day_of_week = current_time.strftime('%A')  # Thứ
        hour = current_time.strftime('%H')         # Giờ
        minute = current_time.strftime('%M')       # Phút
        day = current_time.strftime('%d')          # Ngày
        month = current_time.strftime('%m')        # Tháng
        year = current_time.strftime('%Y')
        
        prompt = f"Please help me check if there is an appointment in this statement. If so, return it in the format: Hour: ..., Minute:..., Day:..., Month:..., Year:... Note the time in 24h format, fill in your answer in the blank and return only the answer without any other characters mixed in. The current time is {hour}:{minute}, {day_of_week}, Day: {day} , Month:{month} , {year}.Apply the mindset of continuity and logic of the week . Below is the sentence to analyze:"
        calendar_input = f"calendar_ {prompt} {input}"
        inputs = {
            "messages": [
                HumanMessage(content=calendar_input)
            ],
        }
        # last_state = dict(list(self.graph.stream(inputs, config=config))[-1])
        # Use async stream
        async for state in self.graph.astream(inputs, config=config):
            last_state = state
            
        response = last_state[list(last_state.keys())[0]]['messages'][0]
        print("response....",response)
        # return response[1:-1] # Due to leading and trailing quotes in the response (to investigate in future.)
        return response
    
    async def chat(self, input: str, config: dict):
        if not self.graph:
            raise ValueError("Graph not initialized. Call initialize_graph first.")
            
        inputs = {
            "messages": [
                HumanMessage(content=input)
            ],
        }
        # last_state = dict(list(self.graph.stream(inputs, config=config))[-1])
        # Use async stream
        print("start chat...")
        async for state in self.graph.astream(inputs, config=config):
            last_state = state
            
        response = last_state[list(last_state.keys())[0]]['messages'][0]
        # return response[1:-1] # Due to leading and trailing quotes in the response (to investigate in future.)
        return response
