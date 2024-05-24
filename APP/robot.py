class Robot:
    def __init__(self, resources, speed, priorities):
        self.resources = resources # items the robot has access to {item: uses} -1 uses means infinite uses left
        self.speed = speed # robots top speed (units per second)
        self.distance_traveled = 0 # total distance traveled
        self.priorities = priorities
