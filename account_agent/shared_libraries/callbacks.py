from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.callback_context import CallbackContext
from typing import Optional, Dict, Any
import random
import time
import re
from services.logger import get_logger
from services.utils import send_otp, update_customer_data
from services.db_service import DBService
from google.genai import types

db = DBService()
logger = get_logger()

      
def before_tool_callback(tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext) -> Optional[Dict[str, str]]:
    """
    A callback function executed before a tool is called.

    This function acts as a security and data-loading middleware. It performs
    the following steps:
    1.  Checks if the tool requires authentication (skips for 'create_account').
    2.  Validates that 'username' and 'password' are present in the tool arguments.
    3.  Verifies the user's credentials against the database.
    4.  If authentication is successful, it fetches the user's full details.
    5.  Populates the 'customer' object in the session state with the user's data.
    6.  Handles any exceptions during the process to prevent crashes.

    Args:
        tool: The tool object that is about to be executed.
        args: A dictionary of arguments provided for the tool call.
        tool_context: The context of the tool, providing access to session state.

    Returns:
        None: If authentication is successful, allowing the tool to proceed.
        Dict[str, str]: A dictionary with an 'error' key if authentication fails
                        or an error occurs. This stops the tool execution and
                        sends the error message back to the agent.
    """
    logger.info(f"before_tool: Executing for tool '{tool.name}'")

    # Tools that do not require authentication can be skipped here.
    tool_name = tool.name
    
    # Creation of user doesnot need 2 factor verification
    if tool_name == "create_account":
        logger.info("Skipping authentication for 'create_account' tool.")
        return None
            # --- Argument Validation ---
    username = args.get("username")
    password = args.get("password")
    user_otp = args.get("user_otp_input", None)
    state = tool_context.state
    state["pending_tool"] = tool_name
    state["pending_args"] = args
    #user_otp_input = tool_context.state.get("user_otp_input", None)

    
    # Extract OTP
    # Natural language OTP fallback
    if user_otp is not None:
        try:
            raw_input = getattr(tool_context, "input", "") or ""
            match = re.search(r"\b(\d{5,6})\b", raw_input)
            if match:
                user_otp = match.group(1)
                args["user_otp"] = user_otp
                logger.info(f"[OTP Extracted from Input] {user_otp}")

            # OTP Verification - Final step for 2 Factor verification
    
            state = tool_context.state
            result = verify_otp(state, username, user_otp, tool_name, args)
            if result["status"] == "OPT_VERIFIED_SUCCESS":
                state["pending_tool"] = None
                state["pending_args"] = None
                state["otp_status"] = None
                return None
            return {"error": "Authentication failed for OTP. Cannot proceed"}
        except Exception as e:
            msg = f"Exception Function: before_tool_callback - OTP SendVerification Failure {e}"
            logger.error(msg)
            return {"error": msg}
    
    try:

        # Initial Call flow for username and password authentication
        if not username or not password:
            logger.warning("Authentication failed: Missing username or password in tool arguments.")
            return {"error": "Authentication failed. Please provide both username and password to proceed."}

        # --- First Level of Verification (Credentials) ---
        logger.info(f"Attempting to verify credentials for user: {username}")
        if not db.verify_user(username, password):
            logger.warning(f"Invalid credentials for user: {username}")
            return {"error": "Authentication failed. Invalid username or password."}
        
        logger.info(f"User '{username}' authenticated successfully via password.")

        # --- Populate Customer Data in Session State ---
        customer = tool_context.state.get("customer")
        if not customer:
             logger.error("Critical: Customer object not found in tool_context state during authentication.")
             return {"error": "A critical session error occurred. Please try starting a new conversation."}

        user_details = db.get_user_details(username)
        if not user_details:
            logger.error(f"Could not retrieve details for authenticated user: {username}")
            return {"error": "Internal error: Failed to load your user profile after login."}

        customer = update_customer_data(user_details, customer)

        # Update the session state with the fully populated customer object
        tool_context.state["customer"] = customer
        logger.info(f"Customer data for '{username}' has been loaded into the session.")

        

    except Exception as e:
        # Log the full exception for debugging purposes
        username_for_log = args.get("username", "unknown")
        logger.error(f"An unexpected error occurred in before_tool for user '{username_for_log}': {e}", exc_info=True)
        # Return a generic error to the user
        return {"error": "An unexpected internal error occurred during the authentication process."}
    # Level 2 verification
    try:
        status = initiating_otp_send(tool_context, args)
        if status is None:
            msg = f"Unable to send OTP for user {username}"
            logger.info(msg)
            return msg
        return {
            "message": status["message"]}
       
    except Exception as e:
        # Log the full exception for debugging purposes
        username_for_log = args.get("username", "unknown")
        msg = f"An unexpected error occurred in Sending OTP in before_tool for user '{username_for_log}': {e}"
        logger.error(msg)
        # Return a generic error to the user
        return {"error": "An unexpected internal error occurred during the authentication process."}

def initiating_otp_send(tool_context, args):
    import time
    import random

    customer = tool_context.state.get("customer")

    user_email = customer.email
    customer = tool_context.state.get("customer")
    if not user_email:
        return {"error": "No email is associated with this account."}

    expected_otp = tool_context.state.get("generated_otp")
    otp_timestamp = tool_context.state.get("otp_timestamp")

    if not expected_otp or not otp_timestamp:
        # Generate and send
        otp = str(random.randint(100000, 999999))

        tool_context.state["generated_otp"] = otp
        tool_context.state["otp_timestamp"] = time.time()
        tool_context.state["otp_status"] = "OTP_PENDING"
        send_otp(user_email, otp)
        logger.info(f"Sent OTP to {user_email}: {otp}")
        return {
            #"status": "OTP_SENT",
            "message": f"An OTP was sent to {user_email}. Please enter it to continue."
        }
        
    return None


from datetime import datetime, timedelta
import os

def verify_otp(state, username, user_otp_input, tool_name, args):
    """
    Verifies the OTP for a given username using session state.
    Returns a structured response indicating next action.
    """
    logger.info(f"verify_otp for {username} ")
    otp_expiry_minutes = int(os.getenv("OTP_EXPIRY_MINUTES", 5))

    if not username:
        return {
            "status": "AUTH_REQUIRED",
            "message": "Username is required for OTP verification."
        }

    otp_info = state.get(username)
    logger.info(f"verify_otp : otp_info {otp_info}")
    if not otp_info:
        return {
            "status": "AUTH_REQUIRED",
            "message": "No OTP challenge found. Please start authentication again."
        }

    # Check OTP expiration
    timestamp = otp_info.get("timestamp")
    if not timestamp or datetime.now() > timestamp + timedelta(minutes=otp_expiry_minutes):
        logger.info(f"OTP for {username} expired.")
        state.pop(username, None)
        return {
            "status": "AUTH_REQUIRED",
            "message": "Your OTP has expired. Please start authentication again."
        }

    # Check user input
    

    if user_otp_input != otp_info.get("otp"):
        return {
            "status": "OTP_PENDING",
            "message": "Invalid OTP. Please try again."
        }

    # OTP verified successfully
    logger.info(f"OTP for {username} verified successfully.")
    state.pop(username, None)

    # Merge any original_args if saved
    original_args = otp_info.get("original_args", {})
    if original_args:
        logger.debug(f"Merging original_args into current args: {original_args}")
        args.update(original_args)

    return {
        "status": "OPT_VERIFIED_SUCCESS",
        "message": f"OTP verified. Proceeding with {tool_name}.",
        "args": args
    }

    
 
