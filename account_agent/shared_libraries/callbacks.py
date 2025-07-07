from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.callback_context import CallbackContext
from google.adk.auth.auth_handler import AuthConfig

from typing import Optional, Dict, Any
import random
import time
from services.logger import get_logger
from services.utils import send_otp, update_customer_data
from services.db_service import DBService


db = DBService()
logger = get_logger()

async def before_agent(callback_context: CallbackContext) -> None:
    try:
        user_id = callback_context.state.get("user_id")
        session_id = callback_context.state.get("session_id")
        app_name = session_id = callback_context.state.get("app_name")

        logger.info(f"before_agent: user_id = {user_id}")
        logger.info(f"before_agent: session_id = {session_id}")
        
            
        #session_deatils = callback_context.session_service.get_session(app_name, user_id, session_id)
        #print(f"before_agent:  {vars(session_deatils)}")
        #if tool.name == "create_account":
        
        return None

    except Exception as e:
        msg = f"Error in before_agent {e}"
        logger.info(msg)
        return

    
def before_tool(
    tool: BaseTool,
    args: Dict[str, Any],
    tool_context: ToolContext
) -> Optional[Dict]:
    
    if tool.name == "create_account":
        return None
    

    logger.info(f"before_tool: {tool.name}")
    username=""
    password=""
    
    customer = tool_context.state.get("customer")
    if customer:
        username = customer.username
        password = customer.password
    
    if customer and customer.otp is None:
        if customer and not customer.username:
            logger.info(f"before_tool: Getting Username and Password to Authenticate")
            username = args.get("username")
            password = args.get("password")
        if not username or not password:
            return {
                "status": "AUTH_REQUIRED",
                "message": "Please provide both username and password to continue."
            }

        user_record = db.verify_user(username, password)
        print(user_record)
        if not user_record or user_record['password'] != password:
            
            logger.warning(f"Authentication failed for user: {username}")
            return {           
                "error": "Authentication failed. Invalid username or password."
            }
        logger.info(f"before_tool: User '{username}' authenticated successfully.")

            # User exists : get all the details
        user_details = db.get_user_details(username)
        logger.info(f"before_tool: database details {user_details}")
        
            # Update the Customer object in the session state
        
        if customer:
            customer.username = username
            customer.password = password
            customer.first_auth = True
            updated_customer = update_customer_data(user_details, customer)
            
            logger.info(f"Customer object in session state updated for user: {username}")
        else:
            logger.warning("Could not find 'customer' object in session state to update.")
        
        # Get OTP
        logger.info(f"before_tool: calling verify_otp_tool")
        verify_otp_tool(args, tool_context, customer)
    
    logger.info(f"before_tool: authenticate_otp")
    return authenticate_otp(args, tool_context, customer)
    #if customer.otp:
    #    return None
    #if status is not None:
    #    msg = f"OTP Authentication Failed for user: {username}"
    #    logger.info(msg)
    #    return msg
    #logger.info(msg)
    #return None


def verify_otp_tool(args, tool_context, customer):
    """Tool that enforces OTP-based email verification with ADK credential flow."""

    #user_email = tool_context.state.get("user_email")
    #user_email = ""
    #if customer:
    #    user_email = customer.email
    customer = tool_context.state.get("customer")
    if customer and customer.otp is None:
        user_email = customer.email
        logger.info(f"verify_otp_tool: customer is {vars(customer)}")
        logger.info(f"verify_otp_tool")
        if not user_email:
            logger.info(f"verify_otp_tool: user email not found")
            return {
                "status": "NO_EMAIL",
                "message": "No email is associated with this user. Please add your email first."
            }
        logger.info(f"verify_otp_tool: Verifying OTP with email {user_email}")
        # Check if we already generated an OTP
        expected_otp = tool_context.state.get("expected_otp",None)
        otp_created_time = tool_context.state.get("otp_created_time", None)

        if expected_otp is None or otp_created_time is None:
            # First invocation: no OTP yet. Generate it.
            otp = str(random.randint(100000, 999999))
            tool_context.state["expected_otp"] = otp
            tool_context.state["otp_created_time"] = time.time()
            logger.info(f"verify_otp_tool: sending OTP {otp}")
            # Simulate sending email
            send_otp(user_email, otp)
            #logger.info(f"verify_otp_tool: Creating AuthConfig")
            # Tell ADK to ask user for OTP input next
            #auth_config = AuthConfig(
            #    name="otp_verification",
            #    description=f"An OTP has been sent to {user_email}. Please enter it to continue.",
            #    authScheme="otp",
            #    fields=[{"name": "user_otp_input", "type": "string"}]
            #)
            #logger.info(f"verify_otp_tool: AuthConfig {auth_config}")
            #tool_context.request_credential(auth_config)

            return f"Please check your email {user_email} for the OTP and enter the OTP to continue."
        

def authenticate_otp(args, tool_context, customer):
    
    expected_otp = tool_context.state.get("expected_otp", None)
    logger.info(f"authenticate_otp: expected OTP {expected_otp}")
    if not expected_otp:
        return["expected_otp"]
    if time.time() - tool_context.state.get("otp_created_time", 0) > 300:
        return {"error": "OTP expired. Please request a new one."}
    user_input_otp = args.get("user_input")
    logger.info(f"authenticate_otp: user_input_otp OTP {user_input_otp}")
    if not user_input_otp:
        return {"error": "Please enter the OTP you received."}

    if user_input_otp == expected_otp:
        logger.info(f"authenticate_otp: correct ")
        tool_context.state["otp_verified"] = True
        return None
    else:
        logger.info(f"error: Incorrect OTP. Please try again. ")
        return {"error": "Incorrect OTP. Please try again."}
        