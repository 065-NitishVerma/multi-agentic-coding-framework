import os
from dotenv import load_dotenv
from autogen import AssistantAgent, UserProxyAgent

load_dotenv()
# api_key = os.getenv("OPENAI_API_KEY")
groq_key = os.getenv("GROQ_API_KEY")

# llm_config = {
#     "config_list": [
#         {
#             "model": "gpt-4o-mini",
#             "api_key": api_key,
#         }
#     ],
#     "temperature": 0.2,
# }

llm_config = {
    "config_list": [
        {
            "model": "llama-3.1-8b-instant",
            "api_key": groq_key,
            "base_url": "https://api.groq.com/openai/v1",
        }
    ],
    "temperature": 0.2,
}

assistant = AssistantAgent(
    name="assistant",
    llm_config=llm_config,
    system_message="You are a helpful assistant.",
)

user = UserProxyAgent(
    name="user",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=2,
    code_execution_config={"use_docker": False}
)

user.initiate_chat(
    assistant,
    message="Write a Python function to check if a number is prime.",
)