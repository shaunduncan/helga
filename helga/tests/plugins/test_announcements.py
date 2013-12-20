import json

from mock import Mock, patch
from pretend import stub

from helga.plugins import announcements


def test_announcement_fails_with_wrong_path():
    request = Mock(path='/foobar')
    resource = announcements.AnnouncementResource(Mock())
    resp = json.loads(resource.render_POST(request))

    assert resp['status'] == 'ERROR'
    assert resp['msg'] == 'Invalid path /foobar'


def test_announcement_no_access_key():
    request = Mock(path='/announce', args={})
    resource = announcements.AnnouncementResource(Mock())
    resp = json.loads(resource.render_POST(request))

    assert resp['status'] == 'ERROR'
    assert resp['msg'] == 'Invalid or missing access key'


def test_announcement_invalid_access_key():
    request = Mock(path='/announce', args={'access_key': ['bar']})
    resource = announcements.AnnouncementResource(Mock())

    with patch('helga.plugins.announcements.settings',
               stub(ANNOUNCEMENT_ACCESS_KEY='foo')):
        resp = json.loads(resource.render_POST(request))

    assert resp['status'] == 'ERROR'
    assert resp['msg'] == 'Invalid or missing access key'


def test_announcement_no_channel_or_message():
    request = Mock(path='/announce', args={'access_key': ['foo']})
    resource = announcements.AnnouncementResource(Mock())

    with patch('helga.plugins.announcements.settings',
               stub(ANNOUNCEMENT_ACCESS_KEY='foo')):
        resp = json.loads(resource.render_POST(request))

    assert resp['status'] == 'ERROR'
    assert resp['msg'] == 'Request missing channel and/or message'


def test_announcement():
    client = Mock()
    request = Mock(path='/announce', args={
        'access_key': ['foo'],
        'channel': ['#bots'],
        'message': ['foobar'],
    })
    resource = announcements.AnnouncementResource(client)

    with patch('helga.plugins.announcements.settings',
               stub(ANNOUNCEMENT_ACCESS_KEY='foo')):
        resp = json.loads(resource.render_POST(request))

    assert resp['status'] == 'OK'
    client.msg.assert_called_with('#bots', 'foobar')
