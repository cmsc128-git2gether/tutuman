from database import get_user_by_email, get_user_by_id

print(get_user_by_email("test@example.com"))
print(get_user_by_id(1))
print(get_user_by_email("nobody@example.com"))
print(get_user_by_id(999))