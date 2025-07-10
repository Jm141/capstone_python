from werkzeug.security import check_password_hash
import user_service

def authenticate_user(email, password):
    user = user_service.get_user_by_email(email)
    if user and check_password_hash(user[8], password):
        if user[9] == 1:  
            return user
        else:
            return 'not_approved'
    return None 