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
    

