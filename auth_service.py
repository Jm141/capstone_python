import user_service

MAX_LOGIN_ATTEMPTS = 3

def authenticate_user(email, password):
    # Check if user is locked
    if user_service.is_user_locked(email):
        return 'locked'
    
    # Check login attempts
    attempts = user_service.get_login_attempts(email)
    if attempts >= MAX_LOGIN_ATTEMPTS:
        user_service.lock_user(email)
        return 'locked'
    
    user = user_service.get_user_by_email(email)
    if user and user_service.verify_password_scrypt(password, user[8]):  # password is at index 8
        # Reset login attempts on successful login
        user_service.reset_login_attempts(email)
        return user
    else:
        # Increment login attempts on failed login
        user_service.increment_login_attempts(email)
        return None 