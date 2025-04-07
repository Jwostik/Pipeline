import os

import uvicorn
import yaml
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import pgmigrate

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

with open("swagger.yaml") as file:
    openapi = yaml.safe_load(file)
    app.openapi_schema = openapi

# abspath = os.path.abspath(__file__)
# dname = os.path.dirname(abspath)
# os.chdir(dname)
# os.system("pgmigrate -t latest migrate")

if __name__ == '__main__':
    uvicorn.run(app)
