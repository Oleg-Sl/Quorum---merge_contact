from threading import Thread, Lock


from . import handler
from .search_duplicate import get_id_duplicate_by_str

lock = Lock()


class ArrayThreads:
    def __init__(self, input_queue, bx24, count_threads):
        self.bx24 = bx24
        self.input_queue = input_queue
        self.count_threads = count_threads
        self.threads = []

    def send_queue_stop_threads(self):
        [self.input_queue.put(None) for _ in range(self.count_threads)]

    def create(self):
        if not self.threads:
            self.threads = [Thread(target=self.handler) for _ in range(self.count_threads)]

    def start(self):
        [thread.start() for thread in self.threads]

    def join(self):
        [thread.join() for thread in self.threads]

    def handler(self):
        pass


class ArrayThreadsGetContacts(ArrayThreads):
    def __init__(self, input_queue, bx24, count_threads):
        super().__init__(input_queue, bx24, count_threads)

    def handler(self):
        while True:
            item = self.input_queue.pop()
            if item is None:
                break

            response = self.bx24.batch(item)
            if 'result' not in response or 'result' not in response['result']:
                continue

            # сохранение полученных контактов в БД
            handler.contacts_create(response['result']['result'], lock)

            self.input_queue.task_done()


class ArrayThreadsBatchGetCompanies(ArrayThreads):
    def __init__(self, input_queue, bx24, count_threads, company_contact_queue):
        self.company_contact_queue = company_contact_queue
        super().__init__(input_queue, bx24, count_threads)

    def handler(self):
        while True:
            item = self.input_queue.pop()
            if item is None:
                break

            response = self.bx24.batch(item)
            if 'result' not in response or 'result' not in response['result']:
                continue

            # сохранение полученных компаний в БД
            handler.companies_create(response['result']['result'], lock, self.company_contact_queue)

            self.input_queue.task_done()


class ArrayThreadsBatchGetCompanyBindContact(ArrayThreads):
    def __init__(self, input_queue, bx24, count_threads):
        super().__init__(input_queue, bx24, count_threads)

    def handler(self):
        while True:
            id_company = self.input_queue.pop()
            if id_company is None:
                break

            response = self.bx24.call('crm.company.contact.items.get', {'id': id_company})

            if 'result' not in response:
                continue

            # сохранение связи компания-контакт в БД
            handler.company_bind_contact(id_company, response['result'], lock)

            self.input_queue.task_done()


class ArrayThreadsMergeContact(ArrayThreads):
    def __init__(self, input_queue, bx24, count_threads, method_merge):
        self.method_merge = method_merge
        super().__init__(input_queue, bx24, count_threads)

    def handler(self):
        while True:
            contact_value = self.input_queue.pop()
            if contact_value is None:
                break

            lock.acquire()
            ids = get_id_duplicate_by_str(contact_value, self.method_merge)
            lock.release()

            handler.merge_contacts(ids, lock)

            self.input_queue.task_done()

