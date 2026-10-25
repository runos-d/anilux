# GET /api/animes/:id/similar

## Примеры

### GET /api/animes/44/similar

### 200

```json
[
  {
    "id": 45,
    "name": "anime_45",
    "russian": "аниме_45",
    "image": {
      "original": "/assets/globals/missing_original.jpg",
      "preview": "/assets/globals/missing_preview.jpg",
      "x96": "/assets/globals/missing_x96.jpg",
      "x48": "/assets/globals/missing_x48.jpg"
    },
    "url": "/animes/45-anime-45",
    "kind": "tv",
    "score": "1.0",
    "status": "released",
    "episodes": 0,
    "episodes_aired": 0,
    "aired_on": null,
    "released_on": null
  }
]
```