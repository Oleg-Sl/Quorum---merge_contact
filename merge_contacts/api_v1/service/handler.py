import json
import os
import base64
from datetime import datetime
from pprint import pprint


from . import bx24_requests
from api_v1.models import Email, Contacts, Companies
from .report import Report


from .variables import TYPE_MERGE_FIELD


bx24 = bx24_requests.Bitrix24()


# добавление контакта в БД
def contacts_create(res_from_bx, lock):
    for _, contacts in res_from_bx.items():
        for contact in contacts:
            emails = []
            if "EMAIL" in contact:
                emails = contact.pop("EMAIL")

            # замена пустых значений на None
            contact = replace_empty_value_with_none__in_dict(contact)

            # сохранение контакта
            lock.acquire()
            contact_item, created = Contacts.objects.update_or_create(**contact)
            lock.release()

            if emails:
                lock.acquire()
                email_create(emails, contact_item)
                lock.release()


# добавление EMAIL в БД
def email_create(emails, contact):
    for email in emails:
        Email.objects.update_or_create(VALUE=email['VALUE'], VALUE_TYPE=email['VALUE_TYPE'], contacts=contact)


# добавление компаний в БД
def companies_create(res_from_bx, lock, company_contact_queue):
    for _, companies in res_from_bx.items():
        for company in companies:
            # сохранение компании
            lock.acquire()
            company_item, created = Companies.objects.update_or_create(**company)
            lock.release()
            company_contact_queue.send_queue(company['ID'])


# связывание записей таблиц контактов и компаний в БД
def company_bind_contact(id_company, contacts, lock):
    for contact in contacts:
        # сохранение компании
        lock.acquire()
        company_obj = Companies.objects.get(ID=id_company)
        contact_obj = Contacts.objects.get(ID=contact['CONTACT_ID'])
        res = company_obj.contacts.add(contact_obj)
        lock.release()


# замена пустых значений на None
def replace_empty_value_with_none__in_dict(d):
    for key in d:
        if not d[key]:
            d[key] = None

    return d


# объединение контактов с переданным списком идентификаторов
def merge_contacts(ids, lock):
    report = Report()
    report.create()
    cmd = {}
    for id_contact in ids:
        cmd[id_contact] = f'crm.contact.get?id={id_contact}'

    response_contacts = bx24.batch(cmd)

    if 'result' not in response_contacts or 'result' not in response_contacts['result']:
        return

    data_update = forming_data_update(response_contacts['result']['result'])
    id_contact_last = get_id_max_date(response_contacts['result']['result'])
    lock.acquire()

    report.add_row(json.dumps(data_update))
    report.add_row(json.dumps(data_update))
    report.add_row(json.dumps(data_update))
    lock.release()
    # pprint(data_update)
    response_update = bx24.call(
        'crm.contact.update',
        {
            'id': id_contact_last,
            'fields': {
                **data_update,
            },
            'params': {"REGISTER_SONET_EVENT": "Y"}
        }
    )

    # pprint(f"{id_contact_last=}")
    # print("99"*8)
    # if response_update.get('result'):
    #     # print("99"*8)
    #     for id_contact in ids:
    #         if int(id_contact) in [id_contact_last, int(id_contact_last)]:
    #             continue
    #         # print(f"{id_contact=}")
    #         res_del = bx24.call(
    #             'crm.contact.delete',
    #             {'id': id_contact}
    #         )
    #         pprint(res_del)


# формирование данных для обновления самого свежего контакта - объединение полей по требуемой логике
def forming_data_update(contacts):
    contacts_update = FieldsContactsUpdate(bx24, contacts)
    data = {}
    fields = get_fields_contact()

    for field, field_data in fields.items():
        if field_data['isReadOnly'] is True:
            continue
        elif field in TYPE_MERGE_FIELD['max_length']:
            data[field] = contacts_update.get_field_rule_max_length(field)
        elif field in TYPE_MERGE_FIELD['concat_asc_date']:
            data[field] = contacts_update.get_field_rule_concat_asc_date(field)
        elif field in TYPE_MERGE_FIELD['concat_desc_date']:
            data[field] = contacts_update.get_field_rule_concat_desc_date(field)
        elif field_data['type'] == 'crm_multifield':
            field_content = contacts_update.get_field_type_crm_multifield(field)
            if field_content:
                data[field] = field_content
        elif field_data['type'] == 'file':
            field_content = contacts_update.get_field_type_file(field)
            if field_content:
                data[field] = field_content
        else:
            field_content = contacts_update.get_field_non_empty(field)
            if field_content:
                data[field] = field_content

    return data


# возвращает идентификатор последнего добавленного контакта
def get_id_max_date(contacts):
    date_create = {}
    for id_contact, contact in contacts.items():
        date_create[id_contact] = datetime.strptime(contact['DATE_CREATE'], '%Y-%m-%dT%H:%M:%S%z')

    return max(date_create, key=date_create.get)


# запрашивает и возвращает список всех полей контакта
def get_fields_contact():
    response_fields = bx24.call('crm.contact.fields', {})
    if 'result' not in response_fields:
        return

    return response_fields['result']


# привязывает к сделке компанию полученную из первого связанного контакта - в Битрикс24
def add_company_in_deal(id_deal):
    response = bx24.batch(
        {
            'deal': f'crm.deal.get?id={id_deal}',
            'contacts': f'crm.deal.contact.items.get?id={id_deal}'
        }
    )

    # print(response)
    if 'result' not in response or 'result' not in response['result']:
        # print('Ответ от биртикс не содержит поле "result"')
        return 400, 'Ответ от биртикс не содержит поле "result"'
    if 'deal' not in response['result']['result']:
        # print('Ответ от биртикс не содержит поле "deal"')
        return 400, 'Ответ от биртикс не содержит поле "deal"'
    if 'contacts' not in response['result']['result']:
        # print('Ответ от биртикс не содержит поле "contacts"')
        return 400, 'Ответ от биртикс не содержит поле "contacts"'

    deal = response['result']['result']['deal']
    contacts = response['result']['result']['contacts']
    company_id = deal.get('COMPANY_ID', None)

    if (company_id and company_id != '0') or not contacts:
        # print('В сделке присутствует связанная компания или отсутствуют контакты')
        return 200, 'В сделке присутствует связанная компания или отсутствуют контакты'

    contact_id = contacts[0].get('CONTACT_ID')

    # Получение данных контакта по его id
    response_contact = bx24.call(
        'crm.contact.get',
        {'id': contact_id}
    )

    if 'result' not in response_contact:
        # print('Ответ на запрос "crm.contact.get" не содержит поле "result"')
        return 400, 'Ответ на запрос "crm.contact.get" не содержит поле "result"'

    contact = response_contact['result']
    company_id = contact.get('COMPANY_ID', None)

    if not company_id:
        return 200, 'К контакту не привязана компания'

    response_deal_update = bx24.call(
        'crm.deal.update',
        {
            'id': id_deal,
            'fields': {
                'COMPANY_ID': company_id
            }
        }
    )

    return 200, 'Ok'


# Класс-примесь - обработки поля по правилу: объединение через ";" от нового к старому
class FieldsContactsFirstNonEmptyAscDate:
    def get_field_non_empty(self, field):
        if self.contacts[self.ids_sort_date[0]].get(field):
            return

        for id_contact in self.ids_sort_date[::-1]:
            value = self.contacts[id_contact].get(field)
            if value:
                return value


# Класс-примесь - обработки поля по правилу: объединение через ";" от нового к старому
class FieldsContactsRuleConcatDescDate:
    def get_field_rule_concat_desc_date(self, field):
        values = []

        for id_contact in self.ids_sort_date[::-1]:
            field_value = self.contacts[id_contact].get(field, '')
            # values.extend([el.strip() for el in field_value.split(';')])
            for el in field_value.split(';'):
                elem = el.strip()
                if elem and elem not in values:
                    values.append(elem)

        return '; '.join(values)


# Класс-примесь - обработки поля по правилу: объединение через ";" от старого к новому
class FieldsContactsRuleConcatAscDate:
    def get_field_rule_concat_asc_date(self, field):
        values = []

        for id_contact in self.ids_sort_date:
            field_value = self.contacts[id_contact].get(field, '')
            # values.extend([el.strip() for el in field_value.split(';') if el])
            for el in field_value.split(';'):
                elem = el.strip()
                if elem and elem not in values:
                    values.append(elem)

        return '; '.join(values)


# Класс-примесь - обработки поля по правилу: наиболее длинное значение
class FieldsContactsRuleMaxLength:
    def get_field_rule_max_length(self, field):
        value = ''
        for id_contact, contact in self.contacts.items():
            if not contact.get(field):
                continue
            if len(contact[field]) > len(value):
                value = contact[field]

        return value


# Класс-примесь - обработки поля с типом CRM_MULTIFIELD (объединение уникальных значений)
class FieldsContactsTypeCrmMultifield:
    def get_field_type_crm_multifield(self, field):
        multifield = []

        for id_contact, contact in self.contacts.items():
            if not contact.get(field):
                continue

            for item in contact[field]:
                if item['VALUE'] not in [d['VALUE'] for d in multifield]:
                    multifield.append({
                        'TYPE_ID': item['TYPE_ID'],
                        'VALUE': item['VALUE'],
                        'VALUE_TYPE': item['VALUE_TYPE']
                    })

        return multifield


# Класс-примесь - обработки поля с типом FILE (получение последнего добавленного)
class FieldsContactsTypeFile:
    def get_field_type_file(self, field):
        field_value = self.contacts[self.id_last_created].get(field)

        # если у нового контакта поле не пустое
        if field_value:
            return

        # перебор от самого свежего контакта к самому старому
        for id_cont in self.ids_sort_date[::-1]:
            field_value = self.contacts[id_cont].get(field)
            # пропуск пустых полей
            if not field_value:
                continue
            # если поле содержит список файлов
            if isinstance(field_value, list):
                return self.get_files(field_value)
            else:
                return self.get_file(field_value)

    def get_files(self, files_items):
        data = []
        for file_item in files_items:
            row_add_file = self.get_file(file_item)
            data.append(row_add_file)

        return data

    def get_file(self, file_item):
        f_name = f'file_{file_item["id"]}'
        f_url = file_item['downloadUrl']
        f_path = self.bx24.download_file(f_url, file_item["id"])
        return {
            "fileData": [
                os.path.split(f_path)[1],
                self.file_to_base64(f_path)
            ]
        }

    @staticmethod
    def file_to_base64(f_path):
        encoded_string = None
        print(f'{f_path=}')
        with open(f_path, "rb") as f:
            encoded_string = base64.b64encode(f.read())

        return encoded_string.decode("ascii")


class FieldsContactsUpdate(FieldsContactsRuleConcatDescDate,
                           FieldsContactsRuleConcatAscDate,
                           FieldsContactsRuleMaxLength,
                           FieldsContactsTypeCrmMultifield,
                           FieldsContactsTypeFile,
                           FieldsContactsFirstNonEmptyAscDate):
    def __init__(self, bx24, contacts):
        self.bx24 = bx24
        self.contacts = contacts
        self.date_format = '%Y-%m-%dT%H:%M:%S%z'
        self.ids_sort_date = None
        self.id_last_created = None

        self.sort_id_by_date()

    def sort_id_by_date(self):
        id_date_list = []
        for id_contact, contact in self.contacts.items():
            date = datetime.strptime(contact['DATE_CREATE'], self.date_format)
            id_date_list.append((id_contact, date))

        id_date_list.sort(key=lambda item: item[1])
        self.ids_sort_date = [id_date[0] for id_date in id_date_list]
        self.id_last_created = self.ids_sort_date[-1]

