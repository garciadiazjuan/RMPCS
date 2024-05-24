class Resource:
    def __init__(self, name, value_left):
        self.name = name
        self.value_left = value_left

    def use(uses):
        # no uses left
        if uses == 0:
            return False
        # infinite uses (default is -1)
        elif uses < 0:
            return True
        # finite non-zero number of uses
        else:
            uses = uses - 1
            return True
