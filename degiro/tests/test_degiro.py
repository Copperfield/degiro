from degiro import Degiro


def test_init(mocker, credentials):
    mock_credentials = mocker.patch('degiro.Degiro._get_credentials')

    client = Degiro()

    assert client.user == {}
    assert client.data is None
    assert client.session
    assert mock_credentials.call_count == 1


def test_get_credentials(credentials):
    Degiro._get_credentials(Degiro)

    assert Degiro.username
    assert Degiro.password


def test_set_session_id():
    set_cookie = "JSESSIONID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.prodx;"
    " Path=/; HttpOnly"

    client = Degiro()
    client._set_session_id(set_cookie)

    assert client.session_id == "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.prodx"


def test_header():
    pass


def test_request():
    pass


def test_login(credentials):
    pass
