import main


def test_patch(mocker):
    mocker.patch('main.mained', return_value=10)
    assert main.mained() == 10
