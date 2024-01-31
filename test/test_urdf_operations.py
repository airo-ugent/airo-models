import airo_models


def check_key_in_urdf(dict_: dict, key: str):
    """Check if a key is in a URDF dictionary."""
    for k, v in dict_.items():
        if k == key:
            return True
        elif isinstance(v, dict):
            if check_key_in_urdf(v, key):
                return True
        elif isinstance(v, list):
            for d in v:
                if check_key_in_urdf(d, key):
                    return True
    return False


def test_delete_key():
    """Test keys are deleted correctly from URDF dictionaries."""
    delete_test_dict = {
        "a": "1",
        "b": {
            "c": "2",
            "d": [{"f": "3"}, {"c": "4"}],
        },
        "e": 5,
    }

    airo_models.urdf.delete_key(delete_test_dict, "c")

    assert check_key_in_urdf(delete_test_dict, "a")
    assert check_key_in_urdf(delete_test_dict, "b")
    assert not check_key_in_urdf(delete_test_dict, "c")
    assert check_key_in_urdf(delete_test_dict, "d")
    assert check_key_in_urdf(delete_test_dict, "e")
    assert check_key_in_urdf(delete_test_dict, "f")
