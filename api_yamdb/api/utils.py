import random


def generate_confirmation_code():
    return str(random.randint(1000000000, 9999999999))