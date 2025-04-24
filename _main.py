import os

import uvicorn
from fastapi.middleware.cors import CORSMiddleware

import models
from pgmigrate import get_config, migrate

from pipeline_routes import app

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

migrations_dir = 'pgmigrate_folder'
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
dbname = os.getenv("DB_NAME")
config = get_config(migrations_dir, models.Migration(target='latest',
                                                     conn=f"host={host} dbname={dbname} user={username} password={password} port={port} connect_timeout=1",
                                                     base_dir=migrations_dir))
migrate(config)


def main():
    uvicorn.run(app)


if __name__ == "__main__":
    main()
