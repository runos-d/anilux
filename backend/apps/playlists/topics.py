TOPIC_GROUPS = [
    {'id': 'occasion', 'name': 'Сценарий просмотра', 'description': 'Для кого или когда смотреть'},
    {'id': 'mood', 'name': 'Настроение', 'description': 'Какое впечатление оставляет подборка'},
]
TOPICS = [
    {'slug': 'beginners', 'name': 'Для новичков', 'group': 'occasion', 'description': 'Понятная отправная точка для знакомства с аниме'},
    {'slug': 'evening', 'name': 'На один вечер', 'group': 'occasion', 'description': 'Короткие истории для одного вечера'},
    {'slug': 'friends', 'name': 'Для компании', 'group': 'occasion', 'description': 'Для совместного просмотра и обсуждения'},
    {'slug': 'cozy', 'name': 'Уютное и спокойное', 'group': 'mood', 'description': 'Мягкие истории, чтобы отдохнуть и расслабиться'},
    {'slug': 'adventure', 'name': 'Дух приключений', 'group': 'mood', 'description': 'Путешествия, открытия и захватывающие приключения'},
    {'slug': 'thoughtful', 'name': 'Есть о чём подумать', 'group': 'mood', 'description': 'Истории, к которым хочется мысленно возвращаться'},
]
TOPIC_BY_SLUG = {topic['slug']: topic for topic in TOPICS}
