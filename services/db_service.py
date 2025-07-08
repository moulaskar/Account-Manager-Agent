import os
import bcrypt
import psycopg2
from psycopg2 import sql
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
from services.logger import get_logger

# Load environment variables
load_dotenv()
logger = get_logger()


class DBService:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT", 5432),
                sslmode="require"  # Enforces SSL/TLS connection for Google Cloud SQL
            )
            logger.info("Database connection established.")
        except psycopg2.OperationalError as e:
            logger.error(f"Error: Could not connect to the database. {e}")
            raise
    

    def verify_user(self, username, password):
        """
        Verifies a user by comparing the provided password with the stored hash.
        Supports bcrypt hashes and plaintext fallback for legacy data.
        """
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(
                    sql.SQL("SELECT username, password FROM {} WHERE username = %s").format(
                        sql.Identifier(os.getenv("DB_TABLE_NAME"))
                    ),
                    (username,)
                )
                user_record = cursor.fetchone()
                if user_record:
                    stored_password = user_record["password"]
                    logger.info(f"Using verification with username and password for: {username}")
                    try:
                        if bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                            logger.info(f"User verified with bcrypt: {username}")
                            return {"username": username}
                    except ValueError:
                        logger.warning(f"Stored password for {username} is not a bcrypt hash. Trying plaintext match.")
                        if password == stored_password:
                            logger.warning(f"User verified with plaintext password: {username}")
                            return {"username": username}
        except Exception as e:
            logger.error(f"Error verifying user {username}: {e}")

        logger.warning(f"Invalid credentials for user: {username}")
        return None

    # ------------- END verify_user
    '''
    def verify_user(self, username, password):
        """
        Verifies a user by comparing the provided password with the stored hash.
        """
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(
                    sql.SQL("SELECT username, password FROM {} WHERE username = %s").format(
                        sql.Identifier(os.getenv("DB_TABLE_NAME"))
                    ),
                    (username,)
                )
                user_record = cursor.fetchone()
                if user_record and bcrypt.checkpw(password.encode('utf-8'), user_record["password"].encode('utf-8')):
                    logger.info(f"User verified: {username}")
                    return {"username": user_record["username"]}
        except Exception as e:
            logger.error(f"Error verifying user {username}: {e}")
        return None
    '''

    def update_field(self, username, field, value):
        """
        Updates a single allowed field for a user.
        """
        allowed_fields = ["email", "password", "phone_number", "address"]
        if field not in allowed_fields:
            logger.error(f"Invalid field specified: {field}")
            raise ValueError(f"Invalid field specified: {field}")

        if field == "password":
            hashed_pw = bcrypt.hashpw(value.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            value_to_update = hashed_pw
        else:
            value_to_update = value

        try:
            with self.conn.cursor() as cursor:
                query = sql.SQL("UPDATE {table} SET {column} = %s WHERE username = %s").format(
                    table=sql.Identifier(os.getenv("DB_TABLE_NAME")),
                    column=sql.Identifier(field)
                )
                cursor.execute(query, (value_to_update, username))
                self.conn.commit()
                logger.info(f"Updated {field} for user {username}")
                return True
        except Exception as e:
            logger.error(f"Error updating {field} for user {username}: {e}")
            #return False
            self.conn.rollback()

    def create_user(self, username, password, **kwargs):
        """
        Creates a new user with hashed password and optional fields.
        """
        if not username or not password:
            logger.error("Username and password are required to create a user.")
            raise ValueError("Username and password are required to create a user.")

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        all_fields = {
            "username": username,
            "password": hashed_pw,
            "first_name": kwargs.get("first_name"),
            "last_name": kwargs.get("last_name"),
            "email": kwargs.get("email"),
            "phone_number": kwargs.get("phone_number"),
            "address": kwargs.get("address")
        }

        columns = list(all_fields.keys())
        values = list(all_fields.values())

        try:
            with self.conn.cursor() as cursor:
                query = sql.SQL(
                    "INSERT INTO {table} ({fields}) VALUES ({placeholders})"
                ).format(
                    table=sql.Identifier(os.getenv("DB_TABLE_NAME")),
                    fields=sql.SQL(", ").join(map(sql.Identifier, columns)),
                    placeholders=sql.SQL(", ").join(sql.Placeholder() * len(columns))
                )
                cursor.execute(query, values)
                self.conn.commit()
                logger.info(f"Created user {username}")
        except Exception as e:
            logger.error(f"Error creating user {username}: {e}")
            self.conn.rollback()

    def get_user_email(self, username):
        """
        Returns the email address for a given username.
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    sql.SQL("SELECT email FROM {} WHERE username = %s").format(
                        sql.Identifier(os.getenv("DB_TABLE_NAME"))
                    ),
                    (username,)
                )
                result = cursor.fetchone()
                if result:
                    logger.info(f"Retrieved email for user {username}")
                    return result[0]
        except Exception as e:
            logger.error(f"Error retrieving email for user {username}: {e}")
        return None

    def get_user_details(self, username):
        """
        Returns all user details as a dictionary.
        """
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute(
                    sql.SQL("SELECT * FROM {} WHERE username = %s").format(
                        sql.Identifier(os.getenv("DB_TABLE_NAME"))
                    ),
                    (username,)
                )
                row = cursor.fetchone()
                if row:
                    logger.info(f"Retrieved details for user {username}")
                    return dict(row)
        except Exception as e:
            logger.error(f"Error retrieving details for user {username}: {e}")
        return None

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")
