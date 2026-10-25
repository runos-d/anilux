---
id: F0035
title: Плеер использует системную картинку в картинке Kodik
status: active
date: '2026-10-16'
tags: [frontend, integrations, verification]
kind: environmental
governed-by: TBD
---

Кнопка «Поверх всех окон» в AnimeWatchView перенесена из наложения на видео в панель под плеером рядом с полноэкранным режимом. Она синхронно отправляет документированный enter_pip текущему KodikPlayer; подтверждение берётся из проверенных по source/origin enter_pip/exit_pip событий. Второй iframe не создаётся и исходное видео не останавливается. Повторное нажатие возвращает видео; таймаут/неподдерживаемый браузер дают видимую ошибку.

В браузере первый вход подтвердил настоящий document.pictureInPictureElement. Это не гарантирует повторный вход: после возврата cross-origin Kodik может требовать новое нажатие внутри видео, поскольку активация кнопки родительского сайта не передаётся iframe. Таймаут сообщает об этом ограничении. Системное окно существует пока открыт исходный сайт/PWA; закрытие исходного плеера завершает PiP.

В нативном Windows-приложении WebView2 выполняет фиксированную медиа-команду с userGesture в проверенном контексте. Живой тест подтвердил три последовательных входа и выхода с паузой 6,5 секунды между циклами: тот же video, paused=false, currentTime продолжает увеличиваться. Таймер устанавливается до отправки команды, чтобы синхронное подтверждение не оставляло ложную ошибку; состояние Android синхронизируется с нативным PiP. Источники и результаты: backend/native/tests/windows_self_test.py; backend/data/local_release/native-webview2/self-test/result.json; docs/NATIVE_APPLICATIONS_REVIEW_2026-10-16.md.

Источники: frontend/src/lib/systemPictureInPicture.ts; frontend/src/components/page/anime/AnimeWatchView.vue; frontend/src/components/Players/KodikPlayer.vue; docs/KODIK_API/PLAYER_API.md; frontend/tests/system-pip-browser.js; docs/API_PWA_REVIEW_2026-10-13.md.
