from queue import Queue
from pprint import pprint


class MyQueue:
    def __init__(self, count_threads):
        self.input_queue = Queue()
        self.count_threads = count_threads
        self.max_size = None

    def send_queue(self, item):
        self.input_queue.put(item)

    def pop(self):
        return self.input_queue.get()

    def task_done(self):
        self.input_queue.task_done()

    def send_queue_stop(self):
        [self.send_queue(None) for _ in range(self.count_threads)]

    def qsize(self):
        return self.input_queue.qsize()

    def set_start_size(self, size_q):
        self.max_size = size_q

    def get_start_size(self):
        return self.max_size


class QueueCommands(MyQueue):
    def __init__(self, method, bx24, count_treads):
        self.method = method
        self.bx24 = bx24
        super().__init__(count_treads)

    def forming(self, fields=[]):
        total = self.bx24.get_count_records(self.method)
        commands = self.bx24.forming_long_batch_commands(self.method, total, fields)
        # pprint(commands)
        cmd_list = self.bx24.split_long_batch_commands(commands)
        # pprint(cmd_list)
        self.set_start_size(len(cmd_list))
        [self.send_queue(cmd) for cmd in cmd_list]
        self.send_queue_stop()


