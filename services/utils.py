from google.genai import types
import random
import smtplib
import random
import os
from email.message import EmailMessage
from services.logger import get_logger



logger = get_logger()


async def process_agent_response(event):
    """Process and return agent's final response text."""
    logger.info(f"process_agent_response: Event ID: {event.id}, Author: {event.author}")

    if not event.content or not event.content.parts:
        logger.info("process_agent_response: No content parts in event")
        return None

    for idx, part in enumerate(event.content.parts):
        if hasattr(part, "text") and part.text and not part.text.isspace():
            logger.info(f"process_agent_response: Part {idx}: '{part.text.strip()}'")

    if event.is_final_response():
        for part in event.content.parts:
            if hasattr(part, "text") and part.text and not part.text.isspace():
                final_response = part.text.strip()
                logger.info("===================== AGENT FINAL RESPONSE ========================")
                logger.info(f"process_agent_response: {final_response}")
                return final_response

    return None



async def call_agent_async(runner, user_id, session_id, query):
    """Call the agent asynchronously with the user's query."""
    content = types.Content(role="user", parts=[types.Part(text=query)])
    
    final_response_text = None
    agent_name = None
    logger.info(f"call_agent_async: Query: {query}")
    try:
        logger.info(f"call_agent_async: user_id: {user_id}  session_id: {session_id}  content: {content}")
        async for event in runner.run_async(
            user_id=user_id, 
            session_id=session_id, 
            new_message=content,
            
        ):
            # Capture the agent name from the event if available
            if event.author:
                agent_name = event.author
            logger.info(f"call_agent_async: user_id: Waiting response from agent: {agent_name}")
            response = await process_agent_response(event)
            logger.info(f"call_agent_async: Agent Response: {response}")
            if response:
                final_response_text = response
        return final_response_text
    except Exception as e:
        msg = f"ERROR during agent run: {e}"
        logger.info(msg)
        print(msg)
        return

    
    

def set_intent(message, session):
    '''
    Set the intent for account management based on user input.
    '''
    try:
        msg_lower = message.lower()
        session.state["intent"] = None

        if "update address" in msg_lower:
            session.state["intent"] = "update_address"
        elif "update email" in msg_lower:
            session.state["intent"] = "update_email"
        elif "update password" in msg_lower:
            session.state["intent"] = "update_password"
        elif "update contact" in msg_lower:
            session.state["intent"] = "update_contact"
        elif "create account" in msg_lower:
            session.state["intent"] = "create_account"

    except Exception as e:
        msg = f"ERROR int set_intent: {e}"
        print(msg)


def get_user_id():
    user_id = str(random.randint(1000, 9999))
    return user_id

def update_customer_data(user_details, customer):
    if user_details:
        customer.username = user_details.get('username', '')
        customer.password = user_details.get('password', '')
        customer.first_name = user_details.get('first_name', '')
        customer.last_name = user_details.get('last_name', '')
        customer.email = user_details.get('email', '')
        customer.new_contact = user_details.get('phone_number', '')
        customer.address = user_details.get('address', '')
    return customer


def send_otp(recipient_email, otp):
    logger.info(f"send_otp: Sending OTP to {recipient_email}")
    msg = EmailMessage()
    msg.set_content(f"Your OTP is: {otp}")
    msg['Subject'] = 'Your OTP for Account Verification'
    msg['From'] = os.getenv("EMAIL_SENDER")
    msg['To'] = recipient_email
    
    with smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT"))) as server:
        server.starttls()
        server.login(os.getenv("EMAIL_SENDER"), os.getenv("SMTP_PASSWORD"))
        server.send_message(msg)
    logger.info(f"send_otp: Sending OTP with message  {msg}")
    return 


def get_instruction():
    
    instruction="""
            - You are an useful Account Manager service agent helping BOT. 
            - You help users with below account services/tools. Mention the actions when you greet the user
                - create account: Create new account for the user by calling create_account.
                - update password: Update password for the user by calling update_password.
                - update email: Update email for the user by calling update_email.
                - update_contact: Update contact for the user by calling update_contact.
                - update_address: Update address for the user by calling update_address.

            - Based on user choice call the appropriate service/tool. 
            - Display to user the success or failure of the action of the service/tool.
            - Keep serving the user till the program runs.
            """
    logger.info(f"Instruction {instruction}")
    return instruction
