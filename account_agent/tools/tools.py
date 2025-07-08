
import json
from services.logger import get_logger
from services.db_service import DBService
from google.adk.tools.tool_context import ToolContext

# Initialize services
db = DBService()
logger = get_logger()


def create_account(
        tool_context: ToolContext,
        username: str,
        password: str,
        first_name: str,
        last_name: str,
        email: str,
        phone_number: str,
        address: str,
) -> str:
    """
    Creates a new user account with the provided details.

    This tool is called when a new user wants to register for an account. It
    collects all necessary personal and contact information and stores it
    securely in the database.

    Args:
        username: The desired username for the new account.
        password: The desired password for the new account.
        first_name: The user's first name.
        last_name: The user's last name.
        email: The user's email address.
        phone_number: The user's phone number.
        address: The user's physical address.

    Returns:
        A string message indicating success or failure of the account creation.
    """
    try:
        logger.info(f"Attempting to create account for username: {username}")
        db.create_user(
            username=username, password=password, first_name=first_name, last_name=last_name, email=email, phone_number=phone_number, address=address
        )
        logger.info(f"Successfully created account for {username}.")

        # Update Customer
        customer = tool_context.state.get("customer")
        customer.username = username
        customer.password = password 
        customer.first_name = first_name
        customer.last_name = last_name
        customer.email = email
        customer.new_contact = phone_number
        customer.address = address
        tool_context.state["customer"] = customer 
        return f"User {username} created successfully."
    except Exception as e:
        logger.error(f"Failed to create user {username}: {e}", exc_info=True)
        return f"Failed to create user {username}: {str(e)}"


def update_contact(tool_context: ToolContext, username: str, password: str, new_phone_number: str) -> str:
    """
    Updates the phone number for an existing user's account.

    This tool requires the user to be authenticated. The `before_tool` callback
    handles authentication, so this function only needs the username and the
    new phone number.

    Args:
        username: The username of the account to update.
        password: The current password for authentication.
        new_phone_number: The new phone number to set for the user.

    Returns:
        A string message indicating the result of the update operation.
    """
    try:
        logger.info(f"Attempting to update phone number for {username}.")
        # Corrected field name from "contact" to "phone_number" to match create_account
        status = db.update_field(username, "phone_number", new_phone_number)
        if status:
            logger.info(f"Successfully updated phone number for {username}.")

            # Update Customer
            customer = tool_context.state.get("customer")
            customer.new_contact = new_phone_number
            tool_context.state["customer"] = customer
            return f"Phone number updated successfully for {username}."
        
        return f"Failed to update phone number for {username}."
    except Exception as e:
        logger.error(f"Failed to update phone number for {username}: {e}", exc_info=True)
        return f"Failed to update phone number for {username}: {str(e)}"


def update_address(tool_context: ToolContext, username: str, password: str, new_address: str) -> str:
    """
    Updates the address for an existing user's account.

    This tool requires the user to be authenticated. The `before_tool` callback
    handles authentication.

    Args:
        username: The username of the account to update.
        password: The current password for authentication.
        new_address: The new address to set for the user.

    Returns:
        A string message indicating the result of the update operation.
    """
    try:
        logger.info(f"Attempting to update address for {username}.")
        status = db.update_field(username, "address", new_address)
        if status:
            logger.info(f"Successfully updated address for {username}.")

            # Update Customer
            customer = tool_context.state.get("customer")
            customer.address = new_address
            tool_context.state["customer"] = customer
            
            return f"Address updated successfully for {username}."
        
        logger.info(f"Failed to update address for {username}")
        return f"Failed to update address for {username}."
    except Exception as e:
        logger.error(f"Failed to update address for {username}: {e}", exc_info=True)
        return f"Failed to update address for {username}: {str(e)}"


def update_email(tool_context: ToolContext, username: str, password: str, new_email: str) -> str:
    """
    Updates the email address for an existing user's account.

    This tool requires the user to be authenticated. The `before_tool` callback
    handles authentication.

    Args:
        username: The username of the account to update.
        password: The current password for authentication.
        new_email: The new email address to set for the user.

    Returns:
        A string message indicating the result of the update operation.
    """
    try:
        logger.info(f"Attempting to update email for {username}.")
        status = db.update_field(username, "email", new_email)
        if status:
            logger.info(f"Successfully updated email for {username}.")

            # Update customer
            customer = tool_context.state.get("customer")
            customer.email = new_email
            tool_context.state["customer"] = customer
            return f"Email updated successfully for {username}."
        return f"Failed to update email for {username}."
    except Exception as e:
        logger.error(f"Failed to update email for {username}: {e}", exc_info=True)
        return f"Failed to update email for {username}: {str(e)}"


def update_password(tool_context: ToolContext, username: str, password: str, new_password: str) -> str:
    """
    Updates the password for an existing user's account.

    This tool requires the user to be authenticated. The `before_tool` callback
    handles authentication.

    Args:
        username: The username of the account to update.
        password: The current password for authentication.
        new_password: The new password to set for the user.

    Returns:
        A string message indicating the result of the update operation.
    """
    try:
        logger.info(f"Attempting to update password for {username}.")
        status = db.update_field(username, "password", new_password)
        if status:
            logger.info(f"Successfully updated password for {username}.")
            # Update customer password in session state
            customer = tool_context.state.get("customer")
            customer.password = new_password
            tool_context.state["customer"] = customer
            return f"Password updated successfully for {username}."
        return f"Failed to update password for {username}."
    except Exception as e:
        logger.error(f"Failed to update password for {username}: {e}", exc_info=True)
        return f"Failed to update password for {username}: {str(e)}"


def inspect_session(tool_context: ToolContext) -> str:
    """
    Logs detailed information about the current session for debugging.

    This tool is for developers to inspect the state of the conversation,
    including session metadata, state variables, and the history of events.
    The output is sent to the application logs.

    Args:
        tool_context: The context of the tool, providing access to the session.

    Returns:
        A string confirming that the session details have been logged.
    """
    session = tool_context.session
    logger.info("--- Inspecting Session ---")
    logger.info(f"Session ID: {session.id}, App: {session.app_name}, User: {session.user_id}")

    # Log session state safely
    try:
        state_str = json.dumps(dict(session.state), default=lambda o: f"<<non-serializable: {type(o).__name__}>>", indent=2)
        logger.info(f"Session State:\n{state_str}")
    except Exception as e:
        logger.error(f"Could not serialize session state: {e}", exc_info=True)

    # Log event history
    logger.info("--- Event History ---")
    if not session.events:
        logger.info("No events in history.")
    else:
        for i, event in enumerate(session.events):
            content_str = "[No content]"
            if event.content and event.content.parts:
                parts_info = [f"Text: '{part.text.strip()}'" for part in event.content.parts if hasattr(part, "text") and part.text and part.text.strip()]
                content_str = "; ".join(parts_info)
            logger.info(f"Event[{i}]: author={event.author}, content='{content_str}'")

    logger.info("--- End of Session Inspection ---")
    return "Session details have been logged."
