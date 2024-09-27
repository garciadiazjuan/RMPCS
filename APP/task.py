import copy
class Task:
    def __init__(self, name, resource_consumes, resource_gives, value,  available, location):
        self.name = name
        self.resource_consumes = resource_consumes # DICT of neccesary consumables (battery %, one time use only items, ...) {item: uses/value used}
        self.resource_gives = resource_gives # dict of items recieved for completing task {item: uses per unit}
        self.value = value # task value recieved
        self.available = available # boolean to keep track of task interdependency
        self.location = location # [A, B] coordinates of task

    # inital test(no constraints)
    def check_if_doable(self, constraints, plan, graph, travel_time):
        robot = copy.deepcopy(plan.robot)
        for resource in robot.resources:
            if resource.name == "time":
                resource.value_left += travel_time
        if self.available & self.check_resources(robot) & self.check_constraints(robot, constraints, plan):
            return True
        return False

    def check_resources(self, robot):
        resources = {}
        for resource in robot.resources:
            resources[resource.name] = resource.value_left
        for resource in self.resource_consumes: # nested loop to check neccesary item overlap
            if resource in resources: # if the item is in robot item
                if self.resource_consumes[resource] > resources[resource]: # make sure robot has enough uses for the item
                    if resources[resource] != -1:
                        return False
            else:
                return False
        return True


    def check_constraints(self, robot, constraints, plan):
        for constraint in constraints["interdependency"]:
            if constraint.task == self:
                if not constraint.check_constraint(plan, robot):
                    return False
        for constraint in constraints["linear"]:
            if not constraint.check_constraint(plan, robot):
                return False
        return True
