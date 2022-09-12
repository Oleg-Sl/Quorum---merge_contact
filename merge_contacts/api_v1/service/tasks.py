import time
from pprint import pprint


from api_v1.models import Email, Contacts, Companies
from . import bx24_requests
from .forming_queues import MyQueue, QueueCommands
from .bx24_threads_requests import (
    ArrayThreadsGetContacts,
    ArrayThreadsBatchGetCompanies,
    ArrayThreadsBatchGetCompanyBindContact,
    ArrayThreadsMergeContact
)
from .search_duplicate import get_duplicates
from .variables import COUNT_THREAD


bx24 = bx24_requests.Bitrix24()

contacts_queue = None
companies_queue = None
company_contact_queue = None
duplicates_queue = None


def merge_contacts(method_merge):
    # Очистка таблиц БД
    clear_database()
    # print(Email.objects.all().count())
    # print(Contacts.objects.all().count())
    # print(Companies.objects.all().count())

    global contacts_queue
    global companies_queue
    global company_contact_queue
    global duplicates_queue

    # Очереди
    contacts_queue = QueueCommands('crm.contact.list', bx24, COUNT_THREAD)
    companies_queue = QueueCommands('crm.company.list', bx24, COUNT_THREAD)
    company_contact_queue = MyQueue(COUNT_THREAD)
    duplicates_queue = MyQueue(COUNT_THREAD)

    # Создание потоков
    threads_contacts = ArrayThreadsGetContacts(contacts_queue, bx24, COUNT_THREAD)
    threads_companies = ArrayThreadsBatchGetCompanies(companies_queue, bx24, COUNT_THREAD, company_contact_queue)
    threads_company_contact = ArrayThreadsBatchGetCompanyBindContact(company_contact_queue, bx24, COUNT_THREAD)
    threads_duplicates = ArrayThreadsMergeContact(duplicates_queue, bx24, COUNT_THREAD, method_merge)

    #
    threads_contacts.create()
    threads_companies.create()
    threads_company_contact.create()
    threads_duplicates.create()

    # Запуск потоков
    threads_contacts.start()
    threads_companies.start()
    threads_company_contact.start()
    threads_duplicates.start()

    # Заполнение очереди запросов - контакты
    contacts_queue.forming([contact.name for contact in Contacts._meta.get_fields()])
    threads_contacts.join()

    # Заполнение очереди запросов получения компаний
    companies_queue.forming([company.name for company in Companies._meta.get_fields()])
    threads_companies.join()

    # Получение данных связи компания-контакт из Битрикс
    company_contact_queue.send_queue_stop()
    threads_company_contact.join()

    duplicates = get_duplicates(method_merge)
    pprint(duplicates)

    # Очередь дубликатов контактов
    duplicates_queue.set_start_size(len(duplicates))
    [duplicates_queue.send_queue(id_contact) for id_contact in duplicates]
    duplicates_queue.send_queue_stop()
    threads_duplicates.join()
    time.sleep(2)
    # print("contacts_queue        > ", contacts_queue.get_start_size())
    # print("contacts_queue        > ", contacts_queue.qsize())
    # print("companies_queue       > ", companies_queue.get_start_size())
    # print("companies_queue       > ", companies_queue.qsize())
    # # print("company_contact_queue > ", company_contact_queue.get_start_size())
    # # print("company_contact_queue > ", company_contact_queue.qsize())
    # print("duplicates_queue      > ", duplicates_queue.get_start_size())
    # print("duplicates_queue      > ", duplicates_queue.qsize())

    print("END!!!")


def clear_database():
    Email.objects.all().delete()
    Contacts.objects.all().delete()
    Companies.objects.all().delete()
