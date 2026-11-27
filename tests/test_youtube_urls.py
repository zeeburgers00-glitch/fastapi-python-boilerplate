from app.services.youtube import video_id

def test_watch_url():
    assert video_id("https://www.youtube.com/watch?v=abcdefghijk") == "abcdefghijk"

def test_short_url():
    assert video_id("https://youtu.be/abcdefghijk") == "abcdefghijk"

def test_shorts_url():
    assert video_id("https://www.youtube.com/shorts/abcdefghijk") == "abcdefghijk"
