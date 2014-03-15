from mock import Mock, patch

from helga.plugins import webhooks


@patch('helga.plugins.webhooks.registry')
def test_route(reg):
    reg.get_plugin.return_value = reg
    fake_fn = lambda: 'foo'
    webhooks.route('/foo', methods=['GET', 'POST'])(fake_fn)

    reg.add_route.assertCalledWith(fake_fn, '/foo', ['GET', 'POST'])


@patch('helga.plugins.webhooks.registry')
def test_route_with_no_methods(reg):
    reg.get_plugin.return_value = reg
    fake_fn = lambda: 'foo'
    webhooks.route('/foo')(fake_fn)

    reg.add_route.assertCalledWith(fake_fn, '/foo', ['GET'])


@patch('helga.plugins.webhooks.settings')
def test_authenticated_passes(settings):
    @webhooks.authenticated
    def fake_fn(*args, **kwargs):
        return 'OK'

    settings.WEBHOOKS_CREDENTIALS = [('foo', 'bar')]

    request = Mock()
    request.getUser.return_value = 'foo'
    request.getPassword.return_value = 'bar'

    assert fake_fn(request) == 'OK'


@patch('helga.plugins.webhooks.settings')
def test_authenticated_fails_when_called(settings):
    @webhooks.authenticated
    def fake_fn(*args, **kwargs):
        return 'OK'

    settings.WEBHOOKS_CREDENTIALS = [('person', 'password')]

    request = Mock()
    request.getUser.return_value = 'foo'
    request.getPassword.return_value = 'bar'

    fake_fn(request)

    request.setRepsonseCode.assertCalledWith(401)
