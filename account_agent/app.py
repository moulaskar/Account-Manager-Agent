import os
import uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.adk.agents import Agent
from google.adk.runners import Runner
from dotenv import load_dotenv
from google.adk.sessions import InMemorySessionService
from .shared_libraries.callbacks import before_tool
from .tools.tools import (
    create_account,
    update_contact,
    update_address,
    update_email,
    update_password,
    inspect_session,
)

session_service = InMemorySessionService()

# Load .env variables
load_dotenv()

# --- Config ---
app_name = os.environ.get("APP_NAME", "Customer Support Agent")

# --- FastAPI setup ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Imports from services ---
from services.logger import setup_logger, get_logger
from services.utils import call_agent_async, set_intent


# --- Root Agent with sub-agents ---
root_agent = Agent(
    name="account_agent",
    model="gemini-2.5-flash",
    global_instruction="Account Management BOT",
    instruction="""
        You are an Account Management assistant.

        Your job is to help users with the following functions:

        - create_account
        - update_password
        - update_email
        - update_contact
        - update_address

        Behavior:

        - If the user asks to do one of these, you must call the matching TOOL with all required arguments.
        - If you do not have enough arguments, ask the user for them.
        - Do not just respond in text when a TOOL is appropriate: always call the TOOL if you can.
        - You can call only one TOOL per user request.
        - Respond conversationally if the user says hello or has a non-tool question.

        Examples:

        - User: "I want to update my email"
        -> Ask for username, password, new_email, then call update_email

        - User: "Create a new account for John Doe"
        -> Ask for all required fields, then call create_account

        If you are unsure which function they want, clarify with the user.
        """,
    tools=[
        create_account,
        update_email,
        update_password,
        update_contact,
        update_address,
    ],
    before_tool_callback=before_tool,
    output_key="conversation"
)
initial_state = {
        "user_id": "1",
        "username": "Guest",
        "conversation": [],
        "first_auth": "",
        "otp": "",
        "sess_id":"",
        "intent": None,
        "address": "",
    }
# --- Runner setup ---
runner = Runner(
    agent=root_agent,
    app_name=app_name,
    session_service=session_service
)

# --- Helper: Generate new session IDs ---
def generate_session_id():
    return str(uuid.uuid4())

# --- Endpoint: Create Session ---
@app.post("/session")
async def create_session_endpoint(request: Request):
    data = await request.json()
    user_id = data.get("user_id", "Guest")
    session_id = generate_session_id()
    
    session = await session_service.create_session(app_name=app_name, user_id=user_id, state=initial_state,session_id=session_id)
    initial_state["sess_id"] = session_id
    initial_state["user_id"] = user_id
   
    setup_logger(session_id)
    logger = get_logger()
    logger.info(f"create_session_endpoint: Session Id: {session_id}")
    logger.info(f"create_session_endpoint: Session created for user: {user_id}")
    logger.info(f"create_session_endpoint: Created Session for user: {vars(session)}")
    return {"session_id": session_id}

# --- Endpoint: Chat ---
@app.post("/chat")
async def chat_with_agent(request: Request):
    data = await request.json()
    user_id = data.get("user_id", "anonymous")
    session_id = data.get("session_id")
    message = data.get("message")
    
    if not message:
        raise HTTPException(status_code=400, detail="No message provided")

    # Auto-create session if missing
    if not session_id:
        session_id = generate_session_id()
        await session_service.create_session(app_name=app_name, user_id=user_id, state=initial_state, session_id=session_id)
        setup_logger(session_id)

    # Ensure logger exists
    setup_logger(session_id)
    logger = get_logger()
    logger.info(f"chat_with_agent: User ({user_id}): {message}")

    # Ensure session exists
    await session_service.create_session(app_name=app_name, user_id=user_id, state=initial_state,session_id=session_id)
    logger.info(f"chat_with_agent: Session created for app_name: {app_name}, user_id: {user_id}, session_id: {session_id}")
    # Call the agent
    await call_agent_async(runner, user_id, session_id, message)
    logger.info(f"------------------------1:  session_id: {session_id}")
    # Get updated session state
    session = await session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
    set_intent(message, session)
    
    logger.info(f"Session State: {session.state}")
 
    
    # Retrieve last agent response
    last_response = session.state.get("conversation")
    logger.info(f"last response: {last_response}")
    if not last_response:
        last_response = "Sorry, I didn't understand that."

    # Maintain conversation history in session
    history = session.state.get("conversation", [])
    #history.append({
    #    "user": message,
    #    "bot": last_response
    #})
    session.state["conversation"] = history

    # Log full conversation so far
    logger.info("============================")
    logger.info(f"Full conversation log")
    logger.info(f"Session ID: {session_id}")
    logger.info(f"User ID: {user_id}")
    logger.info(f'Conversation: {history} ')
    #for i, turn in enumerate(conversation, 1):
    #    logger.info(f"{i}. User: {turn['user']}")
    #    logger.info(f"   Bot: {turn['bot']}")
    #logger.info("============================")

    return {"session_id": session_id, "response": last_response}
