import database.stage_queue
from models import RepeatTimer


if __name__ == '__main__':
    RepeatTimer(1, database.stage_queue.healthcheck, [10]).start()
