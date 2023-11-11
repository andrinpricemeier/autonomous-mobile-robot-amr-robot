class Step:
    def __init__(self, step_number, x1, x2, y):
        self.bricks = []
        self.step_number = step_number
        self.x1 = x1
        self.x2 = x2
        self.y = y
        self.width = abs(x2 - x1)

    def __repr__(self):
        return "[bricks:{0}] step_number: {1}, x1: {2}, x2: {3}, y: {4}".format(
            self.bricks, self.step_number, self.x1, self.x2, self.y
        )

    def __str__(self):
        return "[bricks:{0}] step_number: {1}, x1: {2}, x2: {3}, y: {4}".format(
            self.bricks, self.step_number, self.x1, self.x2, self.y
        )
