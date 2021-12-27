def __getattr__(name):
    """
    Any attribute requested from this module will return None.
    It is not documented which pins exist so hard coding them would only work so far.
    """
    return None
