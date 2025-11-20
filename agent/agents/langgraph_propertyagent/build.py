

from typing import Union, Optional
from langgraph.graph import END, StateGraph, START

from agents.langgraph_propertyagent.graph import graph_nodes, graph_edges, AgentState

from langchain_core.retrievers import BaseRetriever
from langchain_core.language_models.chat_models import BaseChatModel

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver


class workflow():
    
    def __init__(
            self,
            retriever: BaseRetriever,
            llm_model: BaseChatModel,
        ):
        self.retriever = retriever
        self.llm_model = llm_model



    async def initialize_graph(self, checkpointer: Optional[Union[MemorySaver, PostgresSaver]] = None):

        nodes = graph_nodes(retriever=self.retriever, llm_model=self.llm_model)
        edges = graph_edges(llm_model=self.llm_model)


        # Define a new graph
        workflow = StateGraph(AgentState)

        # Define the nodes we will cycle between
        workflow.add_node("retriever", nodes.retrieve_documents)  # agent
        
        # workflow.add_node("rewrite", rewrite)  # Re-writing the question
        workflow.add_node(
            "respond_wContext", nodes.respond_wContext
        )  # Generating a response after we know the documents are relevant
        # Call agent node to decide to retrieve or not
        
        workflow.add_node(
            "respond_woContext", nodes.respond_woContext
        )  # Generating a response after we know the documents are relevant
        # Call agent node to decide to retrieve or not


        workflow.add_edge(START, "retriever")
        
        # workflow.add_edge("evaluation_agent","retrieve")
        # Edges taken after the `action` node is called.
        workflow.add_conditional_edges(
            "retriever",
            # Assess agent decision
            edges.evaluate_retrieved,
        )
        workflow.add_edge("respond_wContext", END)
        workflow.add_edge("respond_woContext", END)

        if checkpointer is None:
            # Compile
            return workflow.compile()
        else:
            return workflow.compile(checkpointer=checkpointer)
    
