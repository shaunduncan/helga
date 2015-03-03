from helga.plugins import ping


def test_ping():
    assert ping.ping('client', 'chan', 'nick', 'msg', 'cmd', 'args') == 'pong'
