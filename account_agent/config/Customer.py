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
        

    @classmethod
    def from_dict(cls, data):
        obj = cls(
            user_id=data.get("user_id"),
            session_id=data.get("session_id"),
            session_service=None,
            app_name=data.get("app_name", "Customer Support Agent")
        )
        obj.session_state = data.get("session_state", {})
        obj.username = data.get("username")
        obj.password = data.get("password")
        obj.first_name = data.get("first_name")
        obj.last_name = data.get("last_name")
        obj.email = data.get("email")
        obj.new_contact = data.get("new_contact")
        obj.address = data.get("address")
        return obj

    def to_dict(self):
        return {
            "username": self.username,
            "password": self.password,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "new_contact": self.new_contact,
            "address": self.address,
        }

    def load_from_dict(self, data: dict):
        self.username = data.get("username")
        self.password = data.get("password")
        self.first_name = data.get("first_name")
        self.last_name = data.get("last_name")
        self.email = data.get("email")
        self.new_contact = data.get("new_contact")
        self.address = data.get("address")
        #self.otp = data.get("otp")
        #self.first_auth = data.get("first_auth")
        #self.logs = data.get("logs")
