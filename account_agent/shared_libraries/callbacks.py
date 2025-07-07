from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from typing import Optional, Dict, Any
import logging
#from ..services.db_service import DBService

#db = DBService()


def before_tool(
    tool: BaseTool,
    args: Dict[str, Any],
    tool_context: ToolContext
) -> Optional[Dict]:
    
    
    username = args.get("username")
    password = args.get("password")
    
    if not username or not password:
        return {
            "status": "AUTH_REQUIRED",
            "message": "Please provide both username and password to continue."
        }
    
    #user_record = db.verify_user(username, password)
    
    #print(user_record)
    #if not user_record or user_record['password'] != password:
    #    print("Inside double_auth_callback: Auth uncesseful")
    #    return {           
    #        "error": "Authentication failed. Invalid username or password."
    #    }
    #print("Inside double_auth_callback: Succesgfully authenticated ")

    return None

