from threading import Timer
import database.stage_queue


class RepeatTimer(Timer):
    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


if __name__ == '__main__':
    RepeatTimer(1, database.stage_queue.execute).start()
