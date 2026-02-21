import os
from flask import Flask
from supabase import create_client, Client
from dotenv import load_dotenv

# load_dotenv()
SUPABASE_URL="https://lejegaygvmjqekkamcrg.supabase.co"
SUPABASE_KEY="sb_publishable_z2he4SSrmXexTRxzioixEg_KdMPWtaH"

app = Flask(__name__)

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

@app.route('/')
def index():
    response = supabase.table('hospitals').select("*").execute()
    todos = response.data

    html = '<h1>Hospitals</h1><ul>'
    for todo in todos:
        html += f'<li>{todo["name"]}</li>'
    html += '</ul>'

    return html

if __name__ == '__main__':
    app.run(debug=True)
