# IndexNow (Яндекс + Bing) -отправка URL после изменения
# Требует API-ключ из .env (INDEXNOW_KEY)
# Дедупликация через Redis (ключ indexnow:{url}, TTL 24ч)
# Endpoint: https://www.indexnow.org/indexnow
