import requests
from icecream import ic


access_token = ''

# URL для запроса
# url = 'https://api.admitad.com/websites/v2//'
# url = 'https://api.admitad.com/advcampaigns//'
url = 'https://api.admitad.com/advcampaigns/website//'


# 35530 Идентификатор партнерской программы

# Параметры запроса (увеличиваем лимит и проверяем другой регион)
params = {
    'region': 'RU',
    'limit': 100,
    # 'website': '',
    'language': 'ru',
}

# Заголовки запроса
headers = {
    'Authorization': f'Bearer {access_token}'
}


def get_campaign():
    # Выполнение GET-запроса
    # url = f'https://api.admitad.com/advcampaigns/{campaign_id}/website//'
    response = requests.get(url, headers=headers, params=params)

    # Проверка ответа
    if response.status_code == 200:
        data = response.json()
        # print(data)
        # ic(data['gotolink'])
        # ic(data['products_csv_link'])
        # ic(data['products_xml_link'])
        # ic(data['advertiser_legal_info'])
        # ic(data['description'])
        print(data)

    else:
        print('Ошибка при выполнении запроса:', response.status_code, response.text)

get_campaign()
