class Customer:
    def __init__(self, user_id, session_id, session_service, app_name):
        self.user_id = user_id
        self.session_id = session_id
        self.session_service = session_service
        self.app_name = app_name
        self.session_state = {}
        self.username = None
        self.password=None,
        self.first_name=None,
        self.last_name=None,
        self.email=None,
        self.new_contact=None,
        self.address=None
        self.otp=None,
        self.first_auth=None,
        self.logs = None

    async def load_from_session(self):
        session = await self.session_service.get_session(
            app_name=self.app_name,
            user_id=self.user_id,
            session_id=self.session_id
        )
        self.session_state = session.state or {}

    async def save_to_session(self):
        session = await self.session_service.get_session(
            app_name=self.app_name,
            user_id=self.user_id,
            session_id=self.session_id
        )
        session.state.update(self.session_state)
