from random import choice


class TestEnv:
    @staticmethod
    def random_item():
        with open('random_items.txt') as f:
            read_data = f.read().split('\n')
            return choice(read_data)

    @staticmethod
    def random_amount():
        with open('random_amount.txt') as f:
            read_data = f.read().split('\n')
            return choice(read_data)
