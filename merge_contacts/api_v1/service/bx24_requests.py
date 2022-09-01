import json
import time
from requests import adapters, post, exceptions

from .bx24_tokens import (update_secrets_bx24, get_secrets_all_bx24, get_secret_bx24)
from .variables import BX24__COUNT_METHODS_IN_BATH, BX24__COUNT_RECORDS_IN_METHODS, COUNT_THREAD
# from variables import

adapters.DEFAULT_RETRIES = 10


class Bitrix24:
    api_url = 'https://{domain}/rest/{method}.json'
    oauth_url = 'https://oauth.bitrix.info/oauth/token/'
    timeout = 60

    def __init__(self):
        tokens = get_secrets_all_bx24()
        self.domain = tokens.get("domain", None)
        self.auth_token = tokens.get("auth_token", None)
        self.refresh_token = tokens.get("refresh_token", None)
        self.client_id = tokens.get("client_id")
        self.client_secret = tokens.get("client_secret")
        self.expires_in = None
        self.length_batch = BX24__COUNT_METHODS_IN_BATH

    def refresh_tokens(self):
        r = {}
        try:
            r = post(
                self.oauth_url,
                params={'grant_type': 'refresh_token', 'client_id': self.client_id, 'client_secret': self.client_secret,
                        'refresh_token': self.refresh_token})
            result = json.loads(r.text)

            self.auth_token = result['access_token']
            self.refresh_token = result['refresh_token']
            self.expires_in = result['expires_in']
            update_secrets_bx24(self.auth_token, self.expires_in, self.refresh_token)
            return True
        except (ValueError, KeyError):
            result = dict(error='Error on decode oauth response [%s]' % r.text)
            return result

    def call(self, method, data):
        try:
            url = self.api_url.format(domain=self.domain, method=method)
            params = dict(auth=self.auth_token)
            headers = {
                'Content-Type': 'application/json',
            }
            r = post(url, data=json.dumps(data), params=params, headers=headers, timeout=self.timeout)
            result = json.loads(r.text)
        except ValueError:
            result = dict(error=f'Error on decode api response [{r.text}]')
        except exceptions.ReadTimeout:
            result = dict(error=f'Timeout waiting expired [{str(self.timeout)} sec]')
        except exceptions.ConnectionError:
            result = dict(error=f'Max retries exceeded [{str(adapters.DEFAULT_RETRIES)}]')

        if 'error' in result and result['error'] in ('NO_AUTH_FOUND', 'expired_token'):
            result_update_token = self.refresh_tokens()
            if result_update_token is not True:
                return result
            result = self.call(method, data)
        elif 'error' in result and result['error'] in ['QUERY_LIMIT_EXCEEDED', ]:
            time.sleep(2)
            return self.call(method, data)

        return result

    def batch(self, cmd):
        if not cmd or not isinstance(cmd, dict):
            return dict(error='Invalid batch structure')

        return self.call(
            'batch',
            {
                "halt": 0,
                "cmd": cmd
            }
        )

    # возвращает количество объектов для заданного списочного метода
    def get_count_records(self, method):
        response = self.call(method, {})
        if response and 'total' in response:
            return response['total']

    # формирование команд для batch запросов
    @staticmethod
    def forming_long_batch_commands(method, total_contacts):
        cmd = {}
        for i in range(0, total_contacts, BX24__COUNT_RECORDS_IN_METHODS):
            cmd[f'key_{i}'] = f'{method}?start={i}'

        return cmd

    # разбивка команд на группы по определенной длине
    def split_long_batch_commands(self, commands):
        count = 0
        cmd = {}
        cmd_list = []
        for key in commands:
            count += 1
            cmd[key] = commands[key]
            if count == self.length_batch:
                cmd_list.append(cmd)
                count = 0
                cmd = {}

        return cmd_list

    # объединение результатов запроса
    @staticmethod
    def merge_long_batch_result(keys, data):
        res = []
        for key in keys:
            res.extend(data.get(key, []))

        return res

    def long_batch(self, method):
        result_batch = []
        # всего записей
        total_contacts = self.get_count_records(method)
        # словарь команд для извлечения всех данных
        commands = self.forming_long_batch_commands(method, total_contacts)
        # список команд для выполнения batch запросов
        cmd_list = self.split_long_batch_commands(commands)
        # выполнение запросов
        for cmd in cmd_list:
            response = self.batch(cmd)
            if 'result' not in response or 'result' not in response['result']:
                continue
            result_batch.extend(self.merge_long_batch_result(cmd.keys(), response['result']['result']))

        return result_batch

