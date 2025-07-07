

import psycopg2
import os
import bcrypt
from psycopg2 import sql
from dotenv import load_dotenv
load_dotenv()
#import logging


class DBService:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT")
            )
        except psycopg2.OperationalError as e:
            print(f"Error: Could not connect to the database. {e}")
            raise

    def verify_user(self, username, password):
        """Verifies a user by comparing the hash of the provided password."""
        
        
        with self.conn.cursor() as cursor:
            cursor.execute(f"""
                SELECT username, password FROM {os.getenv("DB_TABLE_NAME")}
                WHERE username = %s
            """, (username,))
            user_record = cursor.fetchone()
            #if user_record and bcrypt.checkpw(password.encode('utf-8'), user_record[2].encode('utf-8')):
            if user_record and user_record[1] == password:
                # Return id and username, but not the password hash
                return {'username': user_record[0], 'password': user_record[1]}
            
            #return(user_record[0], user_record[1])
        return None

    def update_field(self, username, field, value):
        print("Inside update_field")
        """Updates a single field for a user, protecting against SQL injection."""
        # Whitelist of allowed fields to prevent SQL injection
        allowed_fields = ["email", "password", "contact", "address"]
        if field not in allowed_fields:
            raise ValueError("Error: Invalid field specified for update.")

        # Hash the password if it's the field being updated
        if field == "password":
            hashed_pw = bcrypt.hashpw(value.encode('utf-8'), bcrypt.gensalt())
            value_to_update = hashed_pw.decode('utf-8')
        else:
            value_to_update = value

        with self.conn.cursor() as cursor:
            # Use psycopg2.sql for safe dynamic identifiers
           
            query = sql.SQL("UPDATE {table} SET {column} = %s WHERE username = %s").format(
                table=sql.Identifier(os.getenv("DB_TABLE_NAME")),
                column=sql.Identifier(field)
            )
            cursor.execute(query, (value_to_update, username))
            self.conn.commit()

    def create_user(self, username, password, **kwargs):
        """Creates a new user with required and optional fields, safely."""

        if not username or not password:
            raise ValueError("Username and password are required to create a user.")

        # Hash the password
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Define all fields and default values
        all_fields = {
            "username": username,
            "password": hashed_pw,
            "first_name": kwargs.get("first_name", None),
            "last_name": kwargs.get("last_name", None),
            "email": kwargs.get("email", None),
            "phone_number": kwargs.get("phone_number", None),
            "address": kwargs.get("address", None),
        }

        # Construct the SQL query
        columns = list(all_fields.keys())
        values = list(all_fields.values())

        query = sql.SQL("""
                INSERT INTO {table} ({fields})
                VALUES ({placeholders})
                """).format(
            table=sql.Identifier(os.getenv("DB_TABLE_NAME")),
            fields=sql.SQL(", ").join(map(sql.Identifier, columns)),
            placeholders=sql.SQL(", ").join(sql.Placeholder() * len(columns))
        )

        with self.conn.cursor() as cursor:
            cursor.execute(query, values)
            self.conn.commit()

    def get_user_email(self, user_id):
        with self.conn.cursor() as cursor:
            cursor.execute(f"""
                SELECT email FROM {os.getenv("DB_TABLE_NAME")}
                WHERE id = %s
            """, (user_id,))
            result = cursor.fetchone()
            return result[0] if result else None

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()

