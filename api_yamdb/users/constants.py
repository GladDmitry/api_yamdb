MAX_USERNAME_LENGTH = 150

MAX_EMAIL_LENGTH = 254

MAX_ROLE_LENGTH = 13

USER_ROLE = "user"
MODERATOR_ROLE = "moderator"
ADMIN_ROLE = "admin"

ROLE_CHOICES = (
    (USER_ROLE, "Аутентифицированный пользователь"),
    (MODERATOR_ROLE, "Модератор"),
    (ADMIN_ROLE, "Админ"),
)
