from . import bx24_requests


bx24 = bx24_requests.Bitrix24()


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
        # print('К контакту не привязана компания')
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

    # print(response_deal_update)
    return 200, 'Ok'

