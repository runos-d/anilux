# GET /api/animes/:id/franchise

## Примеры

### GET /api/animes/46/franchise

### 200

```json
{
  "links": [
    {
      "id": 1,
      "source_id": 46,
      "target_id": 47,
      "source": 1,
      "target": 0,
      "weight": 1,
      "relation": "adaptation"
    }
  ],
  "nodes": [
    {
      "id": 47,
      "date": 1669472373,
      "name": "аниме_47",
      "image_url": "/assets/globals/missing_x96.jpg",
      "url": "/animes/47-anime-47",
      "year": null,
      "kind": "TV Сериал",
      "weight": 0
    },
    {
      "id": 46,
      "date": 1669472373,
      "name": "аниме_46",
      "image_url": "/assets/globals/missing_x96.jpg",
      "url": "/animes/46-anime-46",
      "year": null,
      "kind": "TV Сериал",
      "weight": 1
    }
  ],
  "current_id": 46
}
```