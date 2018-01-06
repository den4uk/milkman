try:
	from secrets import token_bytes as token_bytes
except ImportError:
	from os import urandom as token_bytes

# App Settings
SECRET_KEY = token_bytes(32)

# SQL Settings
SQLALCHEMY_DATABASE_URI = 'sqlite:///milk.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# E-Mail Settings
MAIL_SERVER = ''	# eg: smtp.gmail.com
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = ''
MAIL_PASSWORD = ''
