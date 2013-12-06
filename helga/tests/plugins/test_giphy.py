from giphypop import GiphyApiException
from mock import Mock, patch
from pretend import stub

from helga.plugins import giphy


mock_api = Mock()
mock_api.return_value = mock_api
mock_img = stub(media_url='GIF')


@patch('helga.plugins.giphy.Giphy', mock_api)
def test_gifme_returns_random_gif():
    mock_api.return_value = mock_api
    mock_api.random_gif.return_value = mock_img

    resp = giphy.giphy(None, '#bots', 'me', 'helga gifme foo', 'gifme', ['foo'])
    assert mock_api.random_gif.called
    assert resp == mock_img.media_url


@patch('helga.plugins.giphy.Giphy', mock_api)
def test_gifme_returns_translated():
    mock_api.return_value = mock_api
    mock_api.random_gif.side_effect = GiphyApiException
    mock_api.translate.return_value = mock_img

    resp = giphy.giphy(None, '#bots', 'me', 'helga gifme foo', 'gifme', ['foo'])
    assert mock_api.translate.called
    assert resp == mock_img.media_url


@patch('helga.plugins.giphy.Giphy', mock_api)
def test_gifme_returns_searched():
    mock_api.random_gif.side_effect = GiphyApiException
    mock_api.translate.side_effect = GiphyApiException
    mock_api.search_list.return_value = [mock_img]

    resp = giphy.giphy(None, '#bots', 'me', 'helga gifme foo', 'gifme', ['foo'])
    assert mock_api.search_list.called
    assert resp == mock_img.media_url


@patch('helga.plugins.giphy.Giphy', mock_api)
def test_gifme_returns_snark():
    mock_api.random_gif.side_effect = GiphyApiException
    mock_api.translate.side_effect = GiphyApiException
    mock_api.search_list.side_effect = GiphyApiException

    formatted = map(lambda x: x.format(nick='me'), giphy.responses)

    assert giphy.giphy(None, '#bots', 'me', 'helga gifme foo', 'gifme', ['foo']) in formatted
