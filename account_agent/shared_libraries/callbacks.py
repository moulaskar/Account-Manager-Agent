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
from google.genai import types

db = DBService()
logger = get_logger()

'''
def before_agent_callback(callback_context):
    state = callback_context.state
    customer = state.get("customer")
    logger.info(f"before_agent_callback: {vars(customer)}")
    if customer.user_otp is not None:
        
        pending_tool = state.pop("pending_tool", None)
        pending_args = state.pop("pending_args", None)
        msg = f"before_agent_callback: {pending_tool}, {pending_args}"
        logger.info(msg)

        if pending_tool and pending_args:
            state["otp_verified"] = False
            logger.info(f"Resuming original tool call: {pending_tool} with args: {pending_args}")
            return types.Content(
                functionCall=types.FunctionCall(
                    name=pending_tool,
                    args=pending_args
                )
            )
'''       
def before_tool(tool, args, tool_context):
    import time

    logger.info(f"before_tool: {tool.name}")

    if tool.name == "create_account":
        return None
    username = args.get("username")
    password = args.get("password")
    
    logger.info(f"Using verification with username and password for: {username}")
    if not db.verify_user(username, password):
        logger.warning(f"Invalid credentials for user: {username}")
        return {"error": "Authentication failed. Invalid username or password."}
    
    customer = tool_context.state.get("customer")
    user_details = db.get_user_details(username)
    update_customer_data(user_details, customer)

    # update tool context
    tool_context.state["customer"] = customer
    logger.info(f"Customer {username} authenticated.")

    return None


    '''
    customer = tool_context.state.get("customer")
    # Just Username password - Temp for presentation
    if customer.need_otp is False:
        # 2Ensure username and password
        

     

    # ------------ END
    
    if not customer:
        logger.warning("No customer in session.")
        return {"error": "Session error. Please start again."}

    # 1Check for OTP verification flag
    if not customer.otp:
        logger.info("User not yet fully authenticated.")

        # 🟣 SAVE the pending intent if this is the FIRST TIME
        if not tool_context.state.get("pending_tool"):
            logger.info("Saving pending tool and args.")
            tool_context.state["pending_tool"] = tool.name
            tool_context.state["pending_args"] = args
            customer.pending_tool = tool.name
            customer.pending_args = args
          
           


        # 2Ensure username and password
        if not customer.username or not customer.password:
            username = args.get("username")
            password = args.get("password")
            if not username or not password:
                return {
                    "status": "AUTH_REQUIRED",
                    "message": "Please provide your username and password."
                }

            user_record = db.verify_user(username, password)
            if not user_record or user_record['password'] != password:
                logger.warning(f"Invalid credentials for user: {username}")
                return {"error": "Authentication failed. Invalid username or password."}

            # Update customer details
            user_details = db.get_user_details(username)
            update_customer_data(user_details, customer)
            customer.username = username
            customer.password = password
            logger.info(f"Customer {username} authenticated.")
            # No OTP
            return None


        # 3Ensure OTP
        otp_status = verify_otp_tool(args, tool_context, customer)
        if otp_status is not None:
            return otp_status

        # If we get here: user just passed OTP!
        logger.info("OTP verified. Restoring pending tool call.")

        # restore original user intent
        pending_tool = tool_context.state.pop("pending_tool", None)
        pending_args = tool_context.state.pop("pending_args", None)

        if pending_tool and pending_args:
            tool.name = pending_tool
            args.update(pending_args)
            logger.info(f"Resuming tool {tool.name} with args {args}")
            return None

    # Already authenticated
    return None
'''

def verify_otp_tool(args, tool_context, customer):
    import time
    import random

    user_email = customer.email
    customer = tool_context.state.get("customer")
    if not user_email:
        return {"error": "No email is associated with this account."}

    expected_otp = tool_context.state.get("expected_otp")
    otp_timestamp = tool_context.state.get("otp_timestamp")

    if not expected_otp or not otp_timestamp:
        # Generate and send
        otp = str(random.randint(100000, 999999))

        tool_context.state["expected_otp"] = otp
        customer.expected_otp=otp
        tool_context.state["otp_timestamp"] = time.time()
        send_otp(user_email, otp)
        logger.info(f"Sent OTP to {user_email}: {otp}")
        return {
            "status": "OTP_SENT",
            "message": f"An OTP was sent to {user_email}. Please enter it to continue."
        }
    
    while True:
        if time.time() - otp_timestamp > 300:
            tool_context.state.pop("expected_otp", None)
            tool_context.state.pop("otp_timestamp", None)
            return {"error": "OTP expired. Please request a new one."}

        user_input_otp = args.get("user_input")
        #if not user_input_otp:
        #return {"error": "Please enter the OTP you received."}

        if user_input_otp == expected_otp:
            customer.otp = True
            tool_context.state["otp_verified"] = True
            tool_context.state.pop("expected_otp", None)
            tool_context.state.pop("otp_timestamp", None)
            logger.info("OTP verified successfully.")
            return None
        else:
            return {"error": "Incorrect OTP. Please try again."}
    
'''
def after_tool(tool, args, tool_context):
    customer = tool_context.state.get("customer", None)
    if not customer:
        logger.warning("No customer in session.")
        return {"error": "Session error. Please start again."}
    
    otp_state = False
    if customer:
        otp = customer.expected_otp
        if otp:
            
            logger.info(f'Calling verify_user_otp')
            customer.user_otp = message
            status = verify_user_otp(customer)
            if status:
                customer.otp= False
                customer.expected_otp = None
                customer.user_otp = None
                pending_tool = customer.pending_tool
                pending_args = customer.pending_args

                logger.info(f"Resuming original tool call: {pending_tool} with args: {pending_args}")
                return types.Content(
                    functionCall=types.FunctionCall(
                        name=pending_tool,
                        args=pending_args
                    )
                )
            
def verify_user_otp(user_id, session_id,customer):
    expected_otp = customer.expected_otp
    user_input_otp = customer.user_otp
    #otp_timestamp = state.get("otp_timestamp")

    if user_input_otp == expected_otp:
        
        customer.otp = True
   
        logger.info("OTP verified successfully.")
        return True
    else:
        return False
'''

