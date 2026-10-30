from app.api.routes_daily import clean_pulse


def test_pulse_clamped_and_rounded():
    c = clean_pulse({"pulse": {"love": 120, "career": 10, "mood": 61.6, "energy": 50}})
    assert c["pulse"] == {"love": 100, "career": 25, "mood": 62, "energy": 50}


def test_pulse_dropped_when_invalid():
    assert "pulse" not in clean_pulse({"pulse": {"love": "high", "career": 1, "mood": 1, "energy": 1}})
    assert "pulse" not in clean_pulse({"pulse": {"love": 50}})
    assert "pulse" not in clean_pulse({"pulse": [1, 2]})
    assert "pulse" not in clean_pulse({"pulse": {"love": True, "career": 1, "mood": 1, "energy": 1}})


def test_content_without_pulse_untouched():
    assert clean_pulse({"title": "x"}) == {"title": "x"}
