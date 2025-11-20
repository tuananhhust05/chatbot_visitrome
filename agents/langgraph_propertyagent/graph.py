


import time
import json
from datetime import datetime
from langchain.tools.retriever import create_retriever_tool


from langchain_core.retrievers import BaseRetriever
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate


from typing import Annotated, Sequence
from typing_extensions import TypedDict
from typing import List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langchain_core.documents import Document
from database.db import database

import os 
from dotenv import load_dotenv
load_dotenv()



key = os.getenv('KEY')

class AgentState(TypedDict):
    # The add_messages function defines how an update should be processed
    # Default is to replace. add_messages says "append"
    messages: Annotated[Sequence[BaseMessage], add_messages]
    query: str = None
    documents: List[Document] = None
    isUAT: bool = True


# def format_documents(context: List[Document]) -> str:
#     doc="==================Documents=============================\n"
#     for i in range(len(context)):
#         doc += "************************\n" \
#             + "Property Listing ID: " + str(context[i].metadata['doc_id']) + "\n" \
#             + "Property Category: For " + context[i].metadata['category'] + "\n" \
#             + f'Property Notes (Chunk " + {context[i].metadata['chunk_id']} + "): "' + context[i].page_content + '"\n\n'
#     doc +="===============End of Documents=========================\n"
#     return doc
    
def format_documents(context: List[Document]) -> str:
    if not context:
        return "No supporting documents were retrieved."

    doc = "==================Documents=============================\n"

    for document in context:
        doc_id = document.metadata.get('doc_id', 'Unknown ID')
        category = document.metadata.get('category', 'Unknown Category')
        chunk_id = document.metadata.get('chunk_id', 'Unknown Chunk ID')

        doc += (
            "************************\n"
            f"Record ID: {doc_id}\n"
            f"Category: {category}\n"
            f'Chunk {chunk_id}:\n{document.page_content}\n\n'
        )

    doc += "===============End of Documents=========================\n"

    return doc


def _safe_parse_json(raw_payload: str):
    try:
        data = json.loads(raw_payload)
        if isinstance(data, str):
            data = json.loads(data)
        return data
    except Exception:
        return None


def _aggregate_duration(items: List[dict]) -> int:
    duration = 0
    for item in items or []:
        try:
            duration += int(item.get("duration_minutes", 0))
        except (ValueError, TypeError):
            continue
    return duration


def extract_travel_data(context: List[Document]) -> dict:
    travel_data = {"hotels": [], "tours": []}
    if not context:
        return travel_data

    seen_keys = set()
    for document in context:
        payload = _safe_parse_json(document.page_content)
        if not isinstance(payload, dict):
            continue

        category = (document.metadata.get("category", "") or "").lower()
        doc_id = document.metadata.get("doc_id")

        if category == "hotel":
            hotel_id = payload.get("id") or payload.get("hotel_id") or doc_id
            if ("hotel", hotel_id) in seen_keys:
                continue
            seen_keys.add(("hotel", hotel_id))
            travel_data["hotels"].append({
                "id": hotel_id,
                "name": payload.get("name"),
                "city": payload.get("city"),
                "country": payload.get("country"),
                "description": payload.get("des") or payload.get("description"),
                "price_range": payload.get("price_range") or payload.get("price"),
                "link": document.metadata.get("url") or payload.get("link"),
            })

        elif category == "tour":
            tour_id = payload.get("tour_id") or payload.get("id") or doc_id
            if ("tour", tour_id) in seen_keys:
                continue
            seen_keys.add(("tour", tour_id))
            provider = payload.get("provider") or {}
            items = payload.get("items", [])
            travel_data["tours"].append({
                "id": tour_id,
                "name": payload.get("tour_name") or payload.get("name"),
                "city": payload.get("city"),
                "country": payload.get("country"),
                "provider": provider.get("name"),
                "provider_contact": provider.get("contact_email"),
                "link": provider.get("website") or document.metadata.get("url"),
                "highlights": [item.get("location_name") or item.get("description") for item in items if isinstance(item, dict)],
                "duration_minutes": _aggregate_duration(items),
                "items": items,
            })

    return travel_data


class graph_nodes():

    def __init__(
            self,
            retriever: BaseRetriever,
            llm_model: BaseChatModel,
        ):
        self.retriever = retriever
        self.retriever_tool = create_retriever_tool(
            retriever,
            "retrieve_property_data",
            "Search and return information about the property agent's listings.",
        )
        self.tools = [self.retriever_tool]
        self.llm_model = llm_model

    async def retrieve_documents(self, state: AgentState):
        """
        Retrieve documents

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, documents, that contains retrieved documents
        """
        print("---------RETRIEVE---------")
        query = state["messages"][-1].content
        print(f"Query: {query}")

        # Retrieval
        documents = await self.retriever.ainvoke(query)
        return {"documents": documents, "query": query}


    async def respond_wContext(self, state: AgentState):
        """
        Generate answer using query and contextual information.

        Args:
            state (dict): The current state, containing query and documents.

        Returns:
            dict: The updated state with a generated response based on context.
        """
        print("-----RESPOND respond_wContext -----")
        query = state["query"]
        context = state["documents"]

        template = """
        You are VisitRome's AI itinerary concierge.

        Conversation History:
        {history}

        User Query: {query}

        Context Snippets:
        {context}

        Instructions:
        - Reply as an enthusiastic local travel guide, providing helpful information based on the context provided.
        - Use the context snippets to recommend hotels, tours, and activities when relevant.
        - Keep responses natural and conversational, as if you're chatting with a friend planning their trip.
        - Include specific details from the context (names, locations, prices, etc.) when available.
        - If the context contains hotel or tour information, naturally incorporate those recommendations into your response.
        - Never wrap responses in code fences or JSON format.
        - Keep responses concise but informative.

        Provide the final response now.
        """
        prompt = ChatPromptTemplate.from_template(template)

        llm = self.llm_model
        rag_chain = prompt | llm | StrOutputParser()

        query_after = query.split(key)[0]
        convesation_id = query.split(key)[1]
        print("query after", query_after)
        print("conversation_id", convesation_id)
        customList = []
        if "calendar_" in query_after:
            query_after = query_after.replace("calendar_","")
            query_after = query_after.strip()
        else:
            query_find = f"SELECT * FROM messages WHERE conversation_id = {convesation_id} ORDER BY id DESC LIMIT 10"
            messages = await database.fetch_all(query=query_find)
            for mess in messages:
                message = dict(mess)
                customList.append(HumanMessage(content=message["content"]))
        
        print("customList",customList)
        context_text = format_documents(context)
        response = await rag_chain.ainvoke({
            "history": customList,
            "context": context_text,
            "query": query_after
        })

        return {"messages": [f" {response}"]}

    

    async def respond_woContext(self, state: AgentState):
        """
        Generate answer for order checking or quote generation.

        Args:
            state (dict): The current state, containing query and user details.

        Returns:
            dict: The updated state with a response based on the query.
        """
        print("-----RESPOND respond_woContext-----")
        query = state["query"]
        
        template = """
        Conversation History: 
        {history} 

        You are VisitRome's cheerful travel concierge. Provide concise, practical tips using general knowledge when no vector context is available.
        - Keep replies under 5 sentences.
        - Focus on travel logistics, dining, activities, or cultural insights whenever appropriate.
        - If the question is unrelated to travel, still respond helpfully and keep things brief.
        - Never wrap answers in code fences.

        Question: {query}

        Answer:
        """

        print("template", template)
        prompt = ChatPromptTemplate.from_template(template)

        # LLM
        llm = self.llm_model

        # Chain
        rag_chain = prompt | llm | StrOutputParser()

        # Run
        query_after = query.split(key)[0]
        convesation_id = query.split(key)[1]
        print("query after", query_after)
        print("conversation_id", convesation_id)
        
        customList = []
        if "calendar_" in query_after:
            query_after = query_after.replace("calendar_","")
            query_after = query_after.strip()
           
        else:
            query_find = f"SELECT * FROM messages WHERE conversation_id = {convesation_id} ORDER BY id DESC LIMIT 10"
            messages = await database.fetch_all(query=query_find)
            for mess in messages:
                message = dict(mess)
                customList.append(HumanMessage(content=message["content"]))
        
        print("customList",customList)
        response = await rag_chain.ainvoke({"history": customList, "query": query_after})

        print("response",response)
        return {"messages": [f" {response}"]}





from typing import Literal

from langchain import hub
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from pydantic import BaseModel, Field





class graph_edges():

    def __init__(
            self,
            llm_model: BaseChatModel,
        ):
        self.llm_model = llm_model


    async def evaluate_retrieved(self, state: AgentState) -> Literal["respond_wContext", "respond_woContext"]:
        """
        Determines whether the retrieved documents are relevant to the question.

        Args:
            state (AgentState): The current state

        Returns:
            str: A decision for whether the documents are relevant or not
        """

        print("-----CHECK RELEVANCE-----")

        # Data model
        class grade(BaseModel):
            """Binary score for relevance check."""

            binary_score: str = Field(description="Relevance score 'yes' or 'no'")

        # LLM
        model = self.llm_model

        # LLM with tool and validation
        llm_with_tool = model.with_structured_output(grade)

        # Prompt
        prompt = PromptTemplate(
            template="""You are a grader assessing relevance of the retrieved documents to a user query. \n 
            Here is the retrieved document: \n\n {context} \n\n
            Here is the user query: {query} \n
            If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant. \n
            Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question.""",
            input_variables=["context", "query"],
        )

        # Chain
        chain = prompt | llm_with_tool

        query= state["query"]
        context = state["documents"]

        scored_result = await chain.ainvoke({
            "context": format_documents(context),
            "query": query
        })

        score = scored_result.binary_score

        if score == "yes":
            print("DECISION: DOCS RELEVANT")
            return "respond_wContext"

        else:
            print("DECISION: DOCS NOT RELEVANT")
            print(score)
            return "respond_woContext"




