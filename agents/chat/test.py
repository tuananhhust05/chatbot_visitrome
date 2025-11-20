

import os
from langchain_groq import ChatGroq

import weaviate
from langchain.vectorstores import Weaviate

from sentence_transformers import SentenceTransformer

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage



from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver



import pprint

#================================================================================================
# Initialization
#================================================================================================
embedding_model = SentenceTransformer('all-distilroberta-v1')


client = weaviate.Client(
    url="http://localhost:8080"  # Default local Weaviate URL
)



#================================================================================================
# Load tools
#================================================================================================
vectorstore_attrs = ["category", "content", "url", "doc_id", "chunk_id", "agentId"]
weaviate_vectorstore_hotels = Weaviate(
    client=client,
    index_name="Hotels",
    text_key="content",
    attributes=vectorstore_attrs
)
weaviate_vectorstore_tours = Weaviate(
    client=client,
    index_name="Tours",
    text_key="content",
    attributes=vectorstore_attrs
)
# Alias retained for quick manual experiments below
weaviate_vectorstore = weaviate_vectorstore_tours


# Initialize the agent
agent_chat = ChatGroq(
    model="llama-3.3-70b-versatile", 
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
)





#================================================================================================
# Load the workflow
#================================================================================================




#================================================================================================
# No memory conversation
#================================================================================================

# graph = workflow.initialize_graph()

# # Fix input format
# inputs = {
#     "messages": [
#         HumanMessage(content="Do you have properties for rent?")
#     ],
#     "documents": None,
#     "query": None  # Set same as message content
# }
# for output in graph.stream(inputs):
#     for key, value in output.items():
#         pprint.pprint(f"Output from node '{key}':")
#         pprint.pprint("---------")
#         pprint.pprint(value, indent=2, width=80, depth=None)
#     pprint.pprint("\n---------\n")


#================================================================================================
# Memory conversation
#================================================================================================
from langgraph.types import StateSnapshot
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from agents.langchain_integrations.weaviate_retriever import STretriever

from agents.langgraph_propertyagent.build import workflow





retriever = STretriever(
    vectorstore_hotels=weaviate_vectorstore_hotels,
    vectorstore_tours=weaviate_vectorstore_tours,
    embedding_model=embedding_model,
    k=5
)

memory = MemorySaver()

workflow = workflow(retriever=retriever, llm_model=agent_chat)

graphM = workflow.initialize_graph(checkpointer=memory)


config = {"configurable": {"thread_id": "1"}}


def query(input=str):
    inputs = {
        "messages": [
            HumanMessage(content=input)
        ]
    }
    response = dict(list(graphM.stream(inputs, config=config))[-1])
    return response


def print_message_history(snapshot: StateSnapshot):
    print("==================================================")
    for message in snapshot.values['messages']:
        print(message.content)
        print("\n\n==================================================")



query("Do you have properties for sale?")

query("tell me more about the terrace house")


query("yes.")


query("what do you mean?")


query("yes, next tuesday 4pm please.")


query("I want to know everything about the house. including the nails, pins and screws used.")

query("i'm just joking.")


query("not at the moment. what time is our appointment again?")


query("same.")

reponse = query("can you help summarize our discussion?")


snapshot = graphM.get_state(config)

print_message_history(snapshot)








list(reponse.keys())[0]
reponse[list(reponse.keys())[0]]['messages'][0]


def chat(graph: StateGraph, input: str, config: dict):
    inputs = {
        "messages": [
            HumanMessage(content=input)
        ]
    }
    response = dict(list(graph.stream(inputs, config=config))[-1])
    return response







#================================================================================================
#================================================================================================


from agents.chat.property_agent import graph, print_message_history

from langgraph.checkpoint.memory import MemorySaver

import asyncio


memory = MemorySaver()


async def setup():
    agent = graph()
    await agent.intialize_graph(checkpointer=memory)
    return agent

async def run_chat(agent,config,input):
    response = await agent.chat(input, config=config)
    return response



agent = asyncio.run(setup())


response = asyncio.run(run_chat(agent,config,"Do you have properties for rent?"))

response = asyncio.run(run_chat(agent,config,"The one in the newer building sounds fancy. can you share more details?"))

response = asyncio.run(run_chat(agent,config,"Sounds interesting. Is it near a school?"))

response = asyncio.run(run_chat(agent,config,"Yes please."))

response = asyncio.run(run_chat(agent,config,"Yes, what are the available dates?"))

snapshot = agent.graph.get_state(config)

print_message_history(snapshot)





































DB_URI = f"postgresql://{os.environ["POSTGRES_USER"]}:{os.environ["POSTGRES_PASSWORD"]}@{os.environ['POSTGRES_HOST']}:{os.environ['POSTGRES_PORT']}/{os.environ['POSTGRES_DB']}"
connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}
from psycopg_pool import ConnectionPool

with ConnectionPool(
    # Example configuration
    conninfo=DB_URI,
    max_size=10,
    kwargs=connection_kwargs,
) as pool:
    
    checkpointer = PostgresSaver(pool)
    
    # NOTE: you need to call .setup() the first time you're using your checkpointer
    checkpointer.setup()

    graph = workflow.initialize_graph(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "0"}}
    res = chat(graph, "Do you have properties for rent?", config)
    checkpoint = checkpointer.get(config)


res['messages']

checkpoint

res






# Generate query embedding
query = "Do you sell landed properties?"
query_vector = embedding_model.encode(query).tolist()


# Create retriever with explicit vector search
docs = weaviate_vectorstore.similarity_search_by_vector(
    embedding=query_vector,
    k=3
)
docs[2]

weaviate_vectorstore.as_retriever()
#================================================================================================



from agents.langchain_integrations.weaviate_retriever import STretriever

    
retriever = STretriever(
    vectorstore_hotels=weaviate_vectorstore_hotels,
    vectorstore_tours=weaviate_vectorstore_tours,
    embedding_model=embedding_model,
    k=3
)

query = "Do you sell landed properties?"
query = "Do you have properties for rent?"
retriever.invoke(query)


# RAG prompt
template = """Answer the question based only on the following context:
{context}
Question: {question}
"""
prompt = ChatPromptTemplate.from_template(template)


# RAG
# Update chain
chain = (
    RunnableParallel({"context": retriever, "question": RunnablePassthrough()})
    | prompt
    | agent_chat
    | StrOutputParser()
)


# Run query
response = chain.invoke(query)
print(response)











































#================================================================================================
#================================================================================================















