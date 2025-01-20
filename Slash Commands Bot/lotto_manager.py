import time

# Global lotto data
_lotto_data = {
    "is_active": False,
    "participants": [],  # List of participants
    "jackpot": 0,
    "start_time": None,
    "end_time": None,
    "creator": None
}

# Getter for lotto data
def get_lotto_data():
    return _lotto_data

# Setter for lotto data
def set_lotto_data(key, value):
    global _lotto_data
    if key in _lotto_data:
        _lotto_data[key] = value
    else:
        raise KeyError(f"Invalid key: {key}")

# Reset lotto data
def reset_lotto_data():
    global _lotto_data
    _lotto_data = {
        "is_active": False,
        "participants": [],
        "jackpot": 0,
        "start_time": None,
        "end_time": None,
        "creator": None
    }
