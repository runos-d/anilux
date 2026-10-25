import json

from apps.anime.application import kodik_dump_service as k


def _cur(**kw):
    base = dict(pk=1, kodik_id="serial-1", status="ongoing", episodes=5, score=7.0,
                kodik_link="//kodik/serial/1/a", episode_duration=24)
    base.update(kw)
    return k._Cur(**base)


def _group(**kw):
    g = k._new_group()
    g.update(kw)
    return g


def _status(value):
    return {"ongoing": "ongoing", "released": "released", "anons": "announced"}.get(value, "finished")


def test_iter_json_array_across_chunk_boundaries(tmp_path):
    items = [{"id": i, "t": "строка " * (i % 7), "n": {"a": [1, 2, {"b": "]"}]}} for i in range(300)]
    path = tmp_path / "d.json"
    path.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    for chunk in (1, 7, 64, 1 << 20):
        assert list(k.iter_json_array(path, chunk_size=chunk)) == items


def test_iter_json_array_empty_and_truncated(tmp_path):
    empty = tmp_path / "e.json"
    empty.write_text(" [ ] ", encoding="utf-8")
    assert list(k.iter_json_array(empty)) == []
    broken = tmp_path / "b.json"
    broken.write_text('[{"a": 1}, {"b": ', encoding="utf-8")
    try:
        list(k.iter_json_array(broken))
    except k.DumpError:
        return
    raise AssertionError("ожидалась DumpError для оборванного файла")


def test_assert_json_array_rejects_html(tmp_path):
    bad = tmp_path / "x.json"
    bad.write_text("<html>error</html>", encoding="utf-8")
    try:
        k._assert_json_array(bad)
    except k.DumpError:
        return
    raise AssertionError("HTML вместо JSON должен отклоняться")


def test_plan_update_changes_only_allowed_fields():
    group = _group(status="released", status_ts="1", episodes=12, score=8.1,
                   current={"id": "serial-1", "link": "//kodik/serial/1/b", "updated_at": "1"},
                   latest={"id": "serial-9", "link": "//kodik/serial/9/z", "updated_at": "2"})
    changes = k.plan_update(_cur(), group, _status)
    assert changes == {
        "status": "released", "episodes": 12, "total_duration": 12 * 24, "score": 8.1,
        "kodik_link": "//kodik/serial/1/b"
    }


def test_plan_update_no_changes_is_empty():
    group = _group(status="ongoing", episodes=5, score=7.001,
                   current={"id": "serial-1", "link": "//kodik/serial/1/a", "updated_at": "1"})
    assert k.plan_update(_cur(), group, _status) == {}


def test_plan_update_switches_voice_only_on_full_scan():
    group = _group(latest={"id": "serial-9", "link": "//kodik/serial/9/z", "updated_at": "2"})
    assert k.plan_update(_cur(), group, _status, full_scan=True) == {
        "kodik_link": "//kodik/serial/9/z", "kodik_id": "serial-9"}
    assert k.plan_update(_cur(), group, _status, full_scan=False) == {}


def test_plan_update_ignores_missing_values():
    assert k.plan_update(_cur(), _group(), _status) == {}


def test_episodes_total_prefers_total_then_max_of_aired():
    assert k._episodes_total({"material_data": {"episodes_total": 12, "episodes_aired": 3}}) == 12
    assert k._episodes_total({"material_data": {"episodes_total": 0, "episodes_aired": 3},
                              "last_episode": 5, "episodes_count": 4}) == 5
    assert k._episodes_total({"material_data": {}}) is None


def test_normalize_calendar_matches_calendar_view_format():
    raw = [
        {"next_episode": 12, "next_episode_at": "2099-10-02T14:30:00Z", "duration": 23,
         "anime": {"id": "60059", "name": "Nige", "russian": "Беги", "image": {"original": "https://x/o.jpg"}},
         "kind": "tv", "score": 7.57, "status": "ongoing", "episodes": 12, "episodes_aired": 11},
        {"next_episode": 1, "next_episode_at": None, "anime": {"id": "1"}},
        {"anime": {}},
    ]
    entries = k.normalize_calendar(raw)
    assert len(entries) == 1
    e = entries[0]
    assert (e["id"], e["episode"], e["aired_at"], e["russian"], e["poster_url"]) == (
        60059, 12, "2099-10-02T14:30:00Z", "Беги", "https://x/o.jpg")
    assert e["is_upcoming"] is True and e["score"] == 7.57 and e["episodes"] == 12
    assert k.normalize_calendar({"not": "a list"}) == []