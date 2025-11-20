import json
import os
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from scripts_offline.initialize_db.utils.text_processing import load_property_data


    
property_data = load_property_data(filepath='./data/property_info.json')


# Define the instruction for the agent to summarize the data
def instruct_summarize(data):
    messages = [
        SystemMessage(content="""
        The following is information extracted from a property listing webpage. Due to some of the information being extracted from a website, 
        it may not be entirely clear how to piece all the information together. Nevertheless, as a diligent and consciencious individual,
        you will be able to make sense of the information and provide a coherent summary that does not miss out on any important details.
                      
        Other things to take note of:
                      1. Do not keep the topic headers in the summary
                      2. Ensure that the summary is coherent and does not miss out on any important details
                      3. Drop any incomplete information. For example, anonymized information such as phone numbers.
                      4. Omit any mortgage related information (as they are likely incomplete or grossly inaccurate)
                      
        """),
        HumanMessage(content=data),
    ]
    return messages

# Initialize the agent
agent_chat = ChatGroq(
    model="llama-3.3-70b-versatile", 
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
)

# Process the data
for i in range(len(property_data)):
    property_data[i]['processed_data'] = agent_chat.invoke(instruct_summarize(property_data[i]['extracted_data'])).content


# Save the JSON file
with open('./data/property_info_processed.json', 'w', encoding='utf-8') as f:
        json.dump(property_data, f, indent=4, ensure_ascii=False)