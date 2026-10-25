# GET /api/calendar

Show a calendar

## Примеры

### GET /api/calendar

### 200

```json
[
  {
    "next_episode": 1,
    "next_episode_at": "2016-09-04T09:00:00.000+03:00",
    "duration": null,
    "anime": {
      "id": 20,
      "name": "anime_20",
      "russian": "аниме_20",
      "image": {
        "original": "/assets/globals/missing_original.jpg",
        "preview": "/assets/globals/missing_preview.jpg",
        "x96": "/assets/globals/missing_x96.jpg",
        "x48": "/assets/globals/missing_x48.jpg"
      },
      "url": "/animes/20-anime-20",
      "kind": "tv",
      "score": "1.0",
      "status": "ongoing",
      "episodes": 0,
      "episodes_aired": 0,
      "aired_on": "2016-09-04",
      "released_on": null
    }
  },
  {
    "next_episode": 1,
    "next_episode_at": "2016-09-12T09:00:00.000+03:00",
    "duration": null,
    "anime": {
      "id": 26,
      "name": "anime_26",
      "russian": "аниме_26",
      "image": {
        "original": "/assets/globals/missing_original.jpg",
        "preview": "/assets/globals/missing_preview.jpg",
        "x96": "/assets/globals/missing_x96.jpg",
        "x48": "/assets/globals/missing_x48.jpg"
      },
      "url": "/animes/26-anime-26",
      "kind": "tv",
      "score": "1.0",
      "status": "anons",
      "episodes": 0,
      "episodes_aired": 0,
      "aired_on": "2016-09-12",
      "released_on": null
    }
  },
  {
    "next_episode": 1,
    "next_episode_at": "2016-09-19T09:00:00.000+03:00",
    "duration": null,
    "anime": {
      "id": 24,
      "name": "anime_24",
      "russian": "аниме_24",
      "image": {
        "original": "/assets/globals/missing_original.jpg",
        "preview": "/assets/globals/missing_preview.jpg",
        "x96": "/assets/globals/missing_x96.jpg",
        "x48": "/assets/globals/missing_x48.jpg"
      },
      "url": "/animes/24-anime-24",
      "kind": "tv",
      "score": "1.0",
      "status": "anons",
      "episodes": 0,
      "episodes_aired": 0,
      "aired_on": "2016-09-19",
      "released_on": null
    }
  },
  {
    "next_episode": 1,
    "next_episode_at": "2016-09-19T09:00:00.000+03:00",
    "duration": null,
    "anime": {
      "id": 25,
      "name": "anime_25",
      "russian": "аниме_25",
      "image": {
        "original": "/assets/globals/missing_original.jpg",
        "preview": "/assets/globals/missing_preview.jpg",
        "x96": "/assets/globals/missing_x96.jpg",
        "x48": "/assets/globals/missing_x48.jpg"
      },
      "url": "/animes/25-anime-25",
      "kind": "tv",
      "score": "1.0",
      "status": "anons",
      "episodes": 0,
      "episodes_aired": 0,
      "aired_on": "2016-09-19",
      "released_on": null
    }
  }
]
```

---

## Параметры

| Имя параметра | Описание |
| --- | --- |
| `censored` | **необязательно**<br><br>Set to false to allow hentai, yaoi and yuri<br><br>Validations:<br><br>Must be one of: true, false. |