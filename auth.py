# auth.py
# Handles user authentication

def login(username, password):
    """
    Simulates user authentication.
    In a real app, integrate with a database or OAuth.
    """
    return username == "admin" and password == "123"