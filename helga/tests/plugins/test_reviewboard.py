from mock import patch

from helga.plugins import reviewboard


@patch('helga.plugins.reviewboard.settings')
def test_reviewboard(settings):
    settings.REVIEWBOARD_URL = 'http://example.com/{review}'
    expected = 'me might be talking about codereview: http://example.com/1234'
    assert reviewboard.reviewboard(None, '#bots', 'me', 'cr1234', ['1234']) == expected


@patch('helga.plugins.reviewboard.settings')
def test_reviewboard_handles_many(settings):
    settings.REVIEWBOARD_URL = 'http://example.com/{review}'
    expected = 'me might be talking about codereview: http://example.com/123, http://example.com/456'
    assert reviewboard.reviewboard(None, '#bots', 'me', 'cr123 cr456', ['123', '456']) == expected
