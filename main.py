import uvicorn

from pipeline_routes import app

if __name__ == '__main__':
    uvicorn.run(app)
