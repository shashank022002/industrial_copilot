import os
import sys
import time
from dotenv import load_dotenv
from google import genai

from .sop import SYSTEM_PROMPT

# Import the tools we built
from .tools import (
    get_machine_record, 
    summarize_column, 
    compare_groups, 
    failure_breakdown, 
    correlation_analysis, 
    run_sql_query
)

_sessions: dict[str, MaintenanceAgent] = {}

def _get_agent(session_id: str) -> MaintenanceAgent:
    if session_id not in _sessions:
        _sessions[session_id] = MaintenanceAgent()
    return _sessions[session_id]

def ask(session_id: str, message: str) -> dict:
    agent = _get_agent(session_id)

    start = time.perf_counter()
    answer = agent.ask(message)
    latency = time.perf_counter() - start

    return {
        "answer": answer,
        "latency_seconds": latency,
    }

class MaintenanceAgent:
    def __init__(self):
        load_dotenv()
        
        if not os.environ.get("GEMINI_API_KEY"):
            raise ValueError("GEMINI_API_KEY is missing from environment variables.")
        
        model_name = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
        
        self.client = genai.Client()
        
        # Initialize the persistent chat session
        self.chat = self.client.chats.create(
            model=model_name,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                tools=[
                    get_machine_record,
                    summarize_column,
                    compare_groups,
                    failure_breakdown,
                    correlation_analysis,
                    run_sql_query
                ],
                temperature=0.0
            )
        )

    def ask(self, user_prompt: str) -> str:
        """
        Sends the prompt to Gemini. The SDK will automatically pause, execute any 
        required tools locally, append the results, and resume generation until a 
        final text answer is ready.
        """
        try:
            # This single call blocks while the SDK handles all parallel/sequential tool loops
            response = self.chat.send_message(user_prompt)
            return response.text
        except Exception as e:
            return f"Agent execution failed: {str(e)}"

# CLI execution block for testing the tool logic locally
if __name__ == "__main__":
    try:
        agent = MaintenanceAgent()
        print("Industrial Copilot initialized. Type 'exit' to quit.\n")
        
        while True:
            prompt = input("You: ")
            if prompt.lower() in ['exit', 'quit']:
                break
            if not prompt.strip():
                continue
            
            print("Agent is querying the database...")
            answer = agent.ask(prompt)
            print(f"\nCopilot: {answer}\n")
            
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    except Exception as err:
        print(f"Fatal error: {err}")
        sys.exit(1)