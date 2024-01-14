import time
from threading import Thread


class SingletonProcess:
    _instance = None

    def _configure(self):
        self.flag = False
        self.function_thread = Thread()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SingletonProcess, cls).__new__(cls)
            cls._instance._configure()

        return cls._instance

    def _process(self):
        print("Sleeping")
        time.sleep(5)
        print("Not sleeping")

    def long_process(self):
        if self.function_thread.is_alive():
            print("Process is running")
            return
        self.function_thread = Thread(target=self._process)

        self.function_thread.start()


class NotSingleton:
    def __init__(self) -> None:
        self.function_thread = Thread()

    def long_process(self):
        if self.function_thread.is_alive():
            print("Process is running")
            return
        self.function_thread = Thread(target=self._process)

        self.function_thread.start()

    def _process(self):
        print("Sleeping")
        time.sleep(5)
        print("Not sleeping")


if __name__ == "__main__":
    sp = SingletonProcess()

    # sp.long_process()

    sp2 = SingletonProcess()

    # sp2.long_process()
    # sp.long_process()

    # print(sp)
    # print(sp2)

    # sp2.long_process()
    # sp.long_process()

    n = NotSingleton()
    n2 = NotSingleton()

    n.long_process()
    n2.long_process()

    # print(n)
