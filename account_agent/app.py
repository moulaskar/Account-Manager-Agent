import os
import uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.adk.agents import Agent
from google.adk.runners import Runner
from dotenv import load_dotenv
from google.genai import types
from google.adk.sessions import InMemorySessionService
from .shared_libraries.callbacks import before_tool_callback

from .config.Customer import Customer
from .tools.tools import (
    create_account,
    update_contact,
    update_address,
    update_email,
    update_password,
    inspect_session,
)


# Load .env variables
load_dotenv()

# --- Config ---
app_name = os.environ.get("APP_NAME", "Customer Support Agent")
session_service = InMemorySessionService()

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
from services.utils import call_agent_async, set_intent, get_instruction


instructions = get_instruction()
# --- Root Agent with sub-agents ---
root_agent = Agent(
    name="account_agent",
    model="gemini-2.5-flash",
    global_instruction="Account Management BOT",
    instruction="""
        You are an Account Manager service agent. You help users with tools:
        - create_account : creates user account
        - update_password : update user password
        - update_email : update user email
        - update_contact: update contact
        - update_address : update address
        List the tool details to user to choose the correct tool.
        Parse user messages and immediately call the correct service/tool without asking again.
        """,
    tools=[
        create_account,
        update_email,
        update_password,
        update_contact,
        update_address,
    ],
    #before_agent_callback=before_agent_callback,
    before_tool_callback=before_tool_callback,
    output_key="conversation"
)

def get_initial_state(user_id: str, session_id: str) -> dict:
    """Creates the initial state for a new session."""
    customer = Customer(user_id=user_id, session_id=session_id, app_name=app_name)
    initial_state_dict = {
        "pending_tool": None,
        "pending_args": None,
        "otp_status": None,
        "customer": customer,
    }
    
    return initial_state_dict
        

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
    
    state = get_initial_state(user_id, session_id)
    session = await session_service.create_session(
        app_name=app_name, user_id=user_id, state=state, session_id=session_id
    )
   
    setup_logger(session_id)
    logger = get_logger()
    logger.info(f"create_session_endpoint: Session Id: {session_id}")
    logger.info(f"create_session_endpoint: Session created for user: {user_id}")
    logger.info(f"create_session_endpoint: Created Session for user: {vars(session)}")
    return {"session_id": session_id, "initial_message": state.get("conversation")}


@app.post("/chat")
async def chat_with_agent(request: Request):
    try:
        data = await request.json()
        user_id = data.get("user_id", "1234")
        session_id = data.get("session_id")
        message = data.get("message")

        if not message:
            raise HTTPException(status_code=400, detail="No message provided")

        # --- Load or Create Session ---
        if not session_id:
            session_id = generate_session_id()

        session = await session_service.get_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )
        if not session:
            # Session not found: create it
            state = get_initial_state(user_id, session_id)
            session = await session_service.create_session(
                app_name=app_name, user_id=user_id, state=state, session_id=session_id
            )
        else:
            state = session.state

        # --- Setup Logging ---
        setup_logger(session_id)
        logger = get_logger()
        logger.info(f"[CHAT] User requested ({user_id}) says: {message}")

        
        otp_status = state.get("otp_status")
        logger.info(f"Current OTP  STATUS for {user_id} {otp_status}")
        
        if otp_status is not None:
            if state["otp_status"] == "OTP_PENDING":
                pending_tool = state["pending_tool"]
                pending_args = state["pending_args"]

                await runner.run_async(
                    user_id=user_id,
                    session_id=session_id,
                    new_message=types.Content(
                        role="user",
                        parts=[types.Part(function_call=types.FunctionCall(name=pending_tool,args=pending_args))]
                    )
                )

                # Clear pending
                state["pending_tool"] = None
                state["pending_args"] = None
                state["otp_status"] = None

                # Get updated state for response
                updated_session = await session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
                last_response = updated_session.state.get("conversation", "Your request has been processed.")
                return {"session_id": session_id, "response": last_response}
    
        
        # --- Normal Chat Processing ---
        logger.info(f"Working on {message} for session_id: {session_id}")
        await call_agent_async(runner, user_id, session_id, message)
        logger.info(f"[CALL_AGENT] Completed for session_id: {session_id}")

        # Reload updated session state
        updated_session = await session_service.get_session(app_name=app_name, user_id=user_id, session_id=session_id)
        last_response = updated_session.state.get("conversation", "Sorry, I didn't understand that.")

        return {"session_id": session_id, "response": last_response}
        #---------------------------------
        
    except Exception as e:
        msg = f"ERROR in chat_with_agent: {e}"
        logger.error(msg)

