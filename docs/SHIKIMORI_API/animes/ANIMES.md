# GET /api/animes

List animes

Most of parameters can be grouped in lists of values separated by comma:

- `season=2016,2015` – animes with season 2016 year or with season 2015 year
- `kind=tv,movie` – animes with kind TV or with kind Movie

Most of the parameters can be used in the subtraction mode:

- `season=!2016,!2015` – animes without season 2016 year and without season 2015 year
- `kind=!tv,!movie` – animes without kind TV and without kind Movie

Most of the parameters can be used in the combined mode:

- `season=2016,!summer_2016` – animes with season 2016 year and without season summer_2016

## Примеры

### GET /api/animes

### 200

```json
[
  {
    "id": 56,
    "name": "Test",
    "russian": "аниме_56",
    "image": {
      "original": "/assets/globals/missing_original.jpg",
      "preview": "/assets/globals/missing_preview.jpg",
      "x96": "/assets/globals/missing_x96.jpg",
      "x48": "/assets/globals/missing_x48.jpg"
    },
    "url": "/animes/56-test",
    "kind": "tv",
    "score": "8.0",
    "status": "released",
    "episodes": 0,
    "episodes_aired": 0,
    "aired_on": "2014-01-01",
    "released_on": null
  }
]
```

---

## Параметры

| Имя параметра | Описание |
| --- | --- |
| `page` | **необязательно**<br><br>Validations:<br><br>Must be a number between 1 and 100000. |
| `limit` | **необязательно**<br><br>50 maximum<br><br>Validations:<br><br>Must be a number. |
| `order` | **необязательно**<br><br>`id` – by id<br><br>`ranked` – by rank<br><br>`kind` – by type<br><br>`popularity` – by popularity<br><br>`name` – in alphabetical order<br><br>`aired_on` – by release date<br><br>`episodes` – by number of episodes<br><br>`status` – by status<br><br>`random` – by random<br><br>`ranked_random` – by random. Will be removed. Do not use it.<br><br>`ranked_shiki` – by shikimori ranking. Will be removed. Do not use it.<br><br>`updated_at` – by field updated_at on entity. The preview version, there may be problems.<br><br>Validations:<br><br>Must be one of: id, id_desc, ranked, kind, popularity, name, aired_on, episodes, status, random, ranked_random, ranked_shiki, created_at, created_at_desc, updated_at, updated_at_desc. |
| `type` | **необязательно**<br><br>Deprecated |
| `kind` | **необязательно**<br><br>Validations:<br><br>Must be one of: tv, movie, ova, ona, special, tv_special, music, pv, cm, tv_13, tv_24, tv_48 |
| `status` | **необязательно**<br><br>Validations:<br><br>Must be one of: anons, ongoing, released |
| `season` | **необязательно**<br><br>Examples:<br><br>summer_2017<br><br>2016<br><br>2014_2016<br><br>199x |
| `score` | **необязательно**<br><br>Minimal anime score<br><br>Validations:<br><br>Must be a number. |
| `duration` | **необязательно**<br><br>S – less than 10 minutes<br><br>D – less than 30 minutes<br><br>F – more than 30 minutes<br><br>Validations:<br><br>Must be one of: S, D, F |
| `rating` | **необязательно**<br><br>none – No rating<br><br>g – G - All ages<br><br>pg – PG - Children<br><br>pg_13 – PG-13 - Teens 13 or older<br><br>r – R - 17+ recommended (violence & profanity)<br><br>r_plus – R+ - Mild Nudity (may also contain violence & profanity)<br><br>rx – Rx - Hentai (extreme sexual content/nudity)<br><br>Validations:<br><br>Must be one of: none, g, pg, pg_13, r, r_plus, rx |
| `genre` | **необязательно**<br><br>List of genre ids separated by comma |
| `genre_v2` | **необязательно**<br><br>List of genre v2 ids separated by comma |
| `studio` | **необязательно**<br><br>List of studio ids separated by comma |
| `franchise` | **необязательно**<br><br>List of franchises separated by comma |
| `censored` | **необязательно**<br><br>Set to false to allow hentai, yaoi and yuri<br><br>Validations:<br><br>Must be one of: true, false. |
| `mylist` | **необязательно**<br><br>Status of anime in current user list<br><br>Validations:<br><br>Must be one of: planned, watching, rewatching, completed, on_hold, dropped |
| `ids` | **необязательно**<br><br>List of anime ids separated by comma |
| `exclude_ids` | **необязательно**<br><br>List of anime ids separated by comma |
| `search` | **необязательно**<br><br>Search phrase to filter animes by name<br><br>Validations:<br><br>Must be a String |