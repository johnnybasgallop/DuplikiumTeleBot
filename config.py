import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

AUTH_USERNAME = "AJSeducation"
AUTH_TOKEN    = "GM0NGY1ODg2YTFjN2Y0NGY4NzVlMzc"
GET_ACCOUNTS  = "https://www.trade-copier.com/webservice/v4/account/getAccounts.php"

HEADERS = {
    "Auth-Username": AUTH_USERNAME,
    "Auth-Token": AUTH_TOKEN,
    "Accept": "application/json",
}


db = create_client(os.getenv("SUPABASE_PROJECT_URL"), os.getenv("SUPABASE_API_KEY"))
