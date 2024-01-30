from airo_models.dummy import dummy_func


def test_dummy():
    d = dummy_func()
    assert d
