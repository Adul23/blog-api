from decouple import config
SECRET_KEY = config("SECRET_KEY")
ENV_POSSIBLE_OPTIONS = (
    "local",
    "prod",
)
