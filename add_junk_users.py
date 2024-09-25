from app import app
from app.models import db, User
import hashlib
import random
import string

def generate_random_username(length=8):
    """Generate a random username."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def generate_random_password(length=12):
    """Generate a random password."""
    return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=length))

def hash_password(password):
    """Hash the password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def add_junk_users():
    """Add junk users to the database."""
    with app.app_context():
        # Empty the database
        db.session.query(User).delete()
        db.session.commit()
        print("Database emptied.")

        users_added = []  # List to store added users

        # Add 15 junk users
        for i in range(15):
            username = generate_random_username()
            password = generate_random_password()
            hashed_password = hash_password(password)
            
            # Create a new user instance
            new_user = User(username=username, password=hashed_password)
            
            # Add the user to the session
            db.session.add(new_user)
            users_added.append((username, hashed_password))  # Store the added user information

            # Add user 'plankton' after 7 users have been added
            if i == 6:  # After adding the 7th user (index 6)
                plankton_password = 'cf510fcdda3898a5d3708f9582a59df9e4daf55f155fe1a251727225e99adf3d'
                plankton_user = User(username='plankton', password=plankton_password)
                db.session.add(plankton_user)
                print("User 'plankton' added after 7 users.")

        # Commit all changes to the database
        db.session.commit()
        print("15 junk users added successfully.")

        # Print the added users
        print("Users added:")
        for username, hashed_password in users_added:
            print(f"Username: {username}, Password (hashed): {hashed_password}")
        print(f"Username: plankton, Password (hashed): {plankton_password}")

if __name__ == "__main__":
    add_junk_users()
