from os import environ as env

# Flask config
IP = env.get('IP', '0.0.0.0')
PORT = env.get('PORT', 8080)
SERVER_NAME = env.get('SERVER_NAME', 'deadass.csh.rit.edu')
PREFERRED_URL_SCHEME = env.get('PREFERRED_URL_SCHEME', 'https')

# DB Info
DEADASS_URI = env.get('DEADASS_URI', "")
POSTGRES_URI = env.get('POSTGRES_URI', "")
MYSQL_URI = env.get('MYSQL_URI', "")
MONGO_URI = env.get('MONGO_URI', "")
SQLALCHEMY_TRACK_MODIFICATIONS = 'False'

# Openshift secret
SECRET_KEY = env.get("SECRET_KEY", default='SECRET-KEY')

# OpenID Connect SSO config CSH
OIDC_ISSUER = env.get('OIDC_ISSUER', 'https://sso.csh.rit.edu/auth/realms/csh')
OIDC_CLIENT_ID = env.get('OIDC_CLIENT_ID', 'deadass')
OIDC_CLIENT_SECRET = env.get('OIDC_CLIENT_SECRET', 'NOT-A-SECRET')
