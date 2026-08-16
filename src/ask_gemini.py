import os
from dotenv import load_dotenv
from google import genai
from tools import (
    get_machine_record, 
    summarize_column, 
    compare_groups, 
    failure_breakdown, 
    correlation_analysis, 
    run_sql_query
)

class GeminiChatSession:
    def __init__(self, model_name: str = 'gemini-3.5-flash-lite'):
        load_dotenv()
        
        if not os.environ.get("GEMINI_API_KEY"):
            raise ValueError("GEMINI_API_KEY is missing from environment variables.")
        
        self.client = genai.Client()
        
        # Inject the tools into the chat configuration here
        self.chat = self.client.chats.create(
            model=model_name,
            config={
                'tools': [
                    get_machine_record,
                    summarize_column,
                    compare_groups,
                    failure_breakdown,
                    correlation_analysis,
                    run_sql_query
                ]
            }
        )

    def send(self, prompt: str) -> str:
        try:
            response = self.chat.send_message(prompt)
            return response.text
        except Exception as e:
            print(f"API execution failed during send: {e}")
            raise


# Example execution demonstrating context retention
if __name__ == "__main__":
    try:
        chat_session = GeminiChatSession()
        
        print("Sending Prompt 1...")
        reply1 = chat_session.send("Explain early stopping in one sentence.")
        print(f"Gemini: {reply1}\n")
        
        print("Sending Prompt 2...")
        reply2 = chat_session.send("Now compare it to dropout in one sentence.")
        print(f"Gemini: {reply2}\n")
        
    except Exception as err:
        print(f"Application error: {err}")