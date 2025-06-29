import os
import json
from google.generativeai.client import configure
from google.generativeai.generative_models import GenerativeModel
from fastapi import FastAPI, Request
from pydantic import BaseModel
from langgraph.graph import StateGraph
import asyncio

# Set up the Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    configure(api_key=GEMINI_API_KEY)

# Define LangGraph State
class State(BaseModel):
    repo: str
    commit_hash: str
    diff: str
    summary: dict = {}
    efficiency: float = 0.0
    flagged: bool = False

# Define LangGraph node
# Accepts and returns State
async def commit_analysis_node(state: State) -> State:
    repo = state.repo
    commit_hash = state.commit_hash
    diff = state.diff

    prompt = (
        f"You are a code analysis AI. Analyze this git commit diff and return ONLY valid JSON.\n\n"
        f"Repository: {repo}\n"
        f"Commit Hash: {commit_hash}\n"
        f"Diff:\n{diff}\n\n"
        f"Return ONLY this JSON structure (no other text):\n"
        f'{{\n'
        f'  "summary": {{\n'
        f'    "intent": "brief description of what the commit does",\n'
        f'    "changes": "list of specific changes made",\n'
        f'    "observations": "any notable observations about code quality or patterns"\n'
        f'  }},\n'
        f'  "efficiency": 0.75,\n'
        f'  "flagged": false\n'
        f'}}\n\n'
        f"JSON response:"
    )
    
    try:
        loop = asyncio.get_event_loop()
        def sync_call():
            model = GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            return response
        response = await loop.run_in_executor(None, sync_call)
        content = response.text.strip()
        
        # Try to extract JSON from the response
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        # Parse the JSON
        result = json.loads(content)
        
        # Validate required fields
        if "summary" not in result:
            result["summary"] = {"intent": "Unknown", "changes": "Unknown", "observations": "Unknown"}
        if "efficiency" not in result:
            result["efficiency"] = 0.5
        if "flagged" not in result:
            result["flagged"] = False
            
    except Exception as e:
        print(f"AI analysis error: {e}")
        print(f"Raw response: {content if 'content' in locals() else 'No response'}")
        result = {
            "summary": {
                "intent": "Analysis failed",
                "changes": "Could not analyze commit",
                "observations": f"Error: {str(e)}"
            },
            "efficiency": 0.5,
            "flagged": False
        }
    
    # Return a new State with updated fields
    return state.copy(update=result)

# Build LangGraph
graph = StateGraph(State)
graph.add_node("commit_analysis", commit_analysis_node)
graph.set_entry_point("commit_analysis")

# Standalone function for analyzing commits
async def analyze_commit_ai(repo: str, commit_hash: str, diff: str):
    """Analyze a commit using AI"""
    input_state = State(
        repo=repo,
        commit_hash=commit_hash,
        diff=diff
    )
    compiled_graph = graph.compile()
    result_state = await compiled_graph.ainvoke(input_state)
    return {
        "summary": result_state["summary"],
        "efficiency": result_state["efficiency"],
        "flagged": result_state["flagged"]
    }

# FastAPI app setup
app = FastAPI()

@app.post("/analyze")
async def analyze_commit(request: Request):
    payload = await request.json()
    input_state = State(
        repo=payload.get("repo", "unknown-repo"),
        commit_hash=payload.get("commit_hash", "HEAD"),
        diff=payload.get("diff", "")
    )
    compiled_graph = graph.compile()
    result_state = await compiled_graph.ainvoke(input_state)
    # result_state is a dict, not a State object
    return {
        "summary": result_state["summary"],
        "efficiency": result_state["efficiency"],
        "flagged": result_state["flagged"]
    }
