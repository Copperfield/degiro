import os
from degiro import Degiro


def test_get_credentials():
    # set environ vars
    os.environ['username'] = 'test'
    os.environ['password'] = 'passd'

    Degiro._get_credentials(Degiro)

    assert Degiro.username
    assert Degiro.password
