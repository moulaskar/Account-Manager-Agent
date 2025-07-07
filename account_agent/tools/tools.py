
from services.db_service import DBService
from google.adk.tools.tool_context import ToolContext

db = DBService()

def create_account(tool_context: ToolContext, username: str, password: str, first_name: str, last_name: str, email: str, new_contact: str, address: str) -> str:
    """
    Create a new user with only username, password, and contact number.
    Other fields (first_name, last_name, email, address) default to None.
    
    Returns:
        A message indicating whether the user was created successfully or failed.
    """
    
    try:    
        print("Inside create_account")
    #    db.create_user(
    #        username=username,
    #        password=password,
    #        first_name=first_name,
    #        last_name=last_name,
    #        email=email,
    #        phone_number=new_contact,
    #        address=address
    #    )
        return f"User {username} created successfully with contact number."
    except Exception as e:
        return f"Failed to create user {username}: {str(e)}"

def update_contact(username: str, password: str, new_contact: str) -> str:
    """
    Update the user's account contact number 
    Returns:
        A message indicating whether the contact was updated successfully or failed.
    """
    #db.update_field(username, "contact", new_contact)
    return f"Contact updated for {username}."



def update_address(tool_context: ToolContext, username: str, password: str, new_address: str) -> str:
    """
    Update the user's account address. Asks user to enter the input in the same sequence mentioned and seperated by comma
    Returns:
         A message indicating whether the address was updated successfully or failed.
    """
def update_address(tool_context: ToolContext, username: str, password: str, new_address: str) -> str:
    print("Inside update_address: ")
    #print("**********************\n\n\n", vars(tool_context.state))
    customer = tool_context.state.get("customer")
    if customer:
        customer.username = username
        customer.password = password
    db.update_field(username, "address", new_address)
    #intent = tool_context.session.state.get("intent", None)
    #tool_context.state["intext"] = None
    #tool_context.session.state["address"] = new_address
    #return f"Address updated for {username}."



def update_email(username: str, password: str, new_email: str) -> str:
    """
    Update the user's account email.
    Returns:
         A message indicating whether the email was updated successfully or failed.
    """
    print("Inside update_email")
    #db.update_field(username, "email", new_email)
    return f"Email updated for {username}."





def update_password(username: str, password: str, new_password: str) -> str:
    """
    Update the user's account password.
    Returns:
         A message indicating whether the password was updated successfully or failed.
    """
    #db.update_field(username, "password", new_password)
    return f"Password updated for {username}."

def inspect_session(context: ToolContext):
    session = context.session

    # Print session metadata
    print("Session ID:", session.id)
    print("App Name:", session.app_name)
    print("User ID:", session.user_id)
    print("Last Update:", session.last_update_time)

    # Print session state
    print("Session State:", dict(session.state))

    # Print event history
    for event in session.events:
        print("-----")
        print("Author:", event.author)
        print("Text:", getattr(event, "text", ""))
        print("Function Call:", getattr(event, "function_call", None))
        print("Timestamp:", event.timestamp)

    return "Session details logged."
