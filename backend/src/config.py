import os
from dotenv import dotenv_values

# Get the path to the directory this file is in
BASEDIR = os.path.abspath(os.path.dirname(__file__))

# Connect the path with your '.env' file name
env_path = os.path.join(BASEDIR, '..', '.env')
print(f"Looking for .env file at: {env_path}")

# Load the .env file
config = dotenv_values(env_path)

# Get the environment variables
OPENAI_API_KEY = config.get('OPENAI_API_KEY', 'default_key')
AWS_REGION = config.get('AWS_REGION', 'default_region')

print(f"OPENAI_API_KEY: {OPENAI_API_KEY}")
print(f"AWS_REGION: {AWS_REGION}")