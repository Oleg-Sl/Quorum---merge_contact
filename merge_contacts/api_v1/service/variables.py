# Переменные запросов Битрикс24
BX24__COUNT_RECORDS_IN_METHODS = 5      # должно быть 50
BX24__COUNT_METHODS_IN_BATH = 5

COUNT_THREAD = 1

# способы поиска дубликатов
DUPLICATES_FIELDS = {
    'email_company': ['EMAIL__VALUE', 'companies__TITLE'],
    'email_contact_name': ['EMAIL__VALUE', 'NAME'],
}

# способы объединения полей контактов
TYPE_MERGE_FIELD = {
    # 'max_length': ['NAME', ],
    'max_length': ['UF_CRM_1662984998', ],
    # 'concat_asc_date': [],
    'concat_asc_date': ['SOURCE_DESCRIPTION', 'UF_CRM_1662984534', 'UF_CRM_1662984573', 'UF_CRM_1662984592', 'UF_CRM_1662984604'],
    # 'concat_desc_date': ['LAST_NAME',],
    'concat_desc_date': ['UF_CRM_1662984465', ],
    # 'multi_field': ['EMAIL', 'PHONE', ]
    # 'multi_field': ['EMAIL', 'PHONE', ]
}

