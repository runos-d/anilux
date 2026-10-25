# POST /api/v2/episode_notifications

Notify shikimori about anime episode release

## Примеры

### POST /api/v2/episode_notifications

```json
{
  "episode_notification": {
    "aired_at": "2022-11-19T17:19:31+03:00",
    "anime_id": "35",
    "episode": "3",
    "is_anime365": "true",
    "is_fandub": "true",
    "is_raw": "false",
    "is_subtitles": "false"
  },
  "token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

### 200

```json
{
  "id": 1,
  "anime_id": 35,
  "episode": 3,
  "is_raw": false,
  "is_subtitles": false,
  "is_fandub": true,
  "is_anime365": true,
  "topic_id": 123
}
```

---

## Параметры

| Имя параметра | Описание |
| --- | --- |
| `episode_notification` | **необязательно**<br><br>Validations:<br><br>Must be a Hash |
| `episode_notification[anime_id]` | **обязательно**<br><br>Validations:<br><br>Must be a number. |
| `episode_notification[episode]` | **обязательно**<br><br>Validations:<br><br>Must be a number. |
| `episode_notification[aired_at]` | **обязательно**<br><br>Episode release date<br><br>Validations:<br><br>Must be a date in iso8601 YYYY-MM-DDThh:mm:ss±hh format |
| `episode_notification[is_fandub]` | **необязательно**<br><br>Validations:<br><br>Must be one of: true, false, 1, 0. |
| `episode_notification[is_raw]` | **необязательно**<br><br>Validations:<br><br>Must be one of: true, false, 1, 0. |
| `episode_notification[is_subtitles]` | **необязательно**<br><br>Validations:<br><br>Must be one of: true, false, 1, 0. |
| `episode_notification[is_anime365]` | **необязательно**<br><br>Validations:<br><br>Must be one of: true, false, 1, 0. |
| `token` | **обязательно**<br><br>Private token required to access this api<br><br>Validations:<br><br>Must be a String |