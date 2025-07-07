class Customer:
    def __init__(self, user_id, session_id, app_name):
        self.user_id = user_id
        self.session_id = session_id
        #self.session_service = session_service
        self.app_name = app_name
        self.session_state = {}
        self.username = None
        self.password=None
        self.first_name=None
        self.last_name=None
        self.email=None
        self.new_contact=None
        self.address=None
        self.otp=None
        self.first_auth=False
        self.logs = None

    #async def load_from_session(self):
    #    session = await self.session_service.get_session(
    #        app_name=self.app_name,
    #        user_id=self.user_id,
    #        session_id=self.session_id
    #    )
    #    self.session_state = session.state or {}

    #async def save_to_session(self):
    #    session = await self.session_service.get_session(
    #        app_name=self.app_name,
    #        user_id=self.user_id,
    #        session_id=self.session_id
    #    )
    #    session.state.update(self.session_state)

    def to_dict(self):
        return {
            "username": self.username,
            "password": self.password,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "new_contact": self.new_contact,
            "address": self.address,
            "otp": self.otp,
            "first_auth": self.first_auth,
            "logs": self.logs
        }

    def load_from_dict(self, data: dict):
        self.username = data.get("username")
        self.password = data.get("password")
        self.first_name = data.get("first_name")
        self.last_name = data.get("last_name")
        self.email = data.get("email")
        self.new_contact = data.get("new_contact")
        self.address = data.get("address")
        self.otp = data.get("otp")
        self.first_auth = data.get("first_auth")
        self.logs = data.get("logs")
