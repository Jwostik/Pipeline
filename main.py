import os

import uvicorn
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

if os.getenv("DB_CONTAINER") is None:
    load_dotenv()
from pipeline_routes import app

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.chdir("pgmigrate")
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
dbname = os.getenv("DB_NAME")
os.system(
    f"pgmigrate -t latest -c \"host={host} dbname={dbname} user={username} password={password} port={port}\" migrate")

if __name__ == '__main__':
    uvicorn.run(app)
