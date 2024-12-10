import re

def check_password_strength(password):
    """
    Checks the strength of a password and returns a message with its rating.
    
    Criteria:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character (!@#$%^&*()-_+=)
    """
    # Define strength criteria
    length_criteria = len(password) >= 8
    uppercase_criteria = bool(re.search(r'[A-Z]', password))
    lowercase_criteria = bool(re.search(r'[a-z]', password))
    digit_criteria = bool(re.search(r'\d', password))
    special_character_criteria = bool(re.search(r'[!@#$%^&*()\-_=+]', password))
    
    # Evaluate strength
    score = sum([
        length_criteria,
        uppercase_criteria,
        lowercase_criteria,
        digit_criteria,
        special_character_criteria
    ])
    
    # Return feedback
    if score == 5:
        return "Strong password! Your password is secure."
    elif score == 4:
        return "Good password, but you could add more variety for added strength."
    elif score == 3:
        return "Weak password. Consider adding more characters, numbers, or special characters."
    else:
        return "Very weak password! Consider using a longer password with a mix of letters, numbers, and special characters."
