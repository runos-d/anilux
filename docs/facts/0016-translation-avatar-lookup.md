---
id: F0016
title: Документация и lookup аватарок расходятся
status: active
date: '2026-10-11'
tags:
- media
- frontend
- documentation
kind: environmental
governed-by: D0014
---

Инструкция описывает API → assets/translation-avatars и транслитерацию. translationAvatars.ts фактически строит URL `/media/translation-logos/{slug}.png` по EXT_MAP и сохраняет кириллицу; AnimeDetailView/AnimeWatchView вызывают этот helper. Инструкцию нельзя считать доказательством assets fallback.

Источники: `frontend/src/assets/translation-avatars/README.md`, `frontend/src/assets/translation-avatars/INSTRUCTIONS.md`, `frontend/src/utils/translationAvatars.ts`, `frontend/src/components/page/anime/AnimeDetailView.vue`, `frontend/src/components/page/anime/AnimeWatchView.vue`.
