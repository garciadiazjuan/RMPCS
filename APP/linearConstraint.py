class LinearConstraint:
    def __init__(self, name, resource, initial_value, upper_limit, lower_limit, penalty_value, priority_value):
        self.name = name
        self.resource = resource # resource name
        self.initial_value = initial_value # int
        self.upper_limit = upper_limit # int
        self.lower_limit = lower_limit # int
        self.penalty_value = penalty_value # dict
        self.current_penalty = 0
        self.priority_value = priority_value # int that acts as a key for the robots preference to penalty list

    def check_applicable_limit(self):
        if not self.upper_limit == None and not self.lower_limit== None:
            return "both"
        elif self.upper_limit:
            return "upper"
        return "lower"

    def check_constraint(self, plan, robot):
        boundary = self.check_applicable_limit()
        resource_name = self.resource
        for resource in robot.resources:
            if resource.name == resource_name:
                if boundary == "both":
                    if resource.value_left < self.upper_limit and resource.value_left > self.lower_limit:
                        return True
                elif boundary == "upper":
                    if resource.value_left < self.upper_limit:
                        return True
                elif boundary == "lower":
                    if resource.value_left > self.lower_limit:
                        return True
                if self.priority_value == '0': # priority 1 means hard boundary
                    return False
        return True

    def update_penalty(self, plan, robot):
        # select which boundary is broken, then use coefficient and priorities to calculate penalty
        self.current_penalty = 0
        value_left = 0
        for resource in robot.resources:
            if resource.name == self.resource:
                value_left = resource.value_left
        boundary = self.check_applicable_limit()
        if boundary == "both":
            upper_constraint_violation = abs((value_left-self.initial_value)/(self.upper_limit-self.initial_value))
            lower_constraint_violation = abs((self.initial_value- value_left)/(self.initial_value-self.lower_limit))
            if upper_constraint_violation >= 1:
                self.current_penalty += self.penalty_value + (upper_constraint_violation - 1)  * robot.priorities[self.priority_value]
            if lower_constraint_violation >= 1:
                self.current_penalty += self.penalty_value + (lower_constraint_violation - 1)  * robot.priorities[self.priority_value]
        elif boundary == "upper":
            upper_constraint_violation = abs((value_left-self.initial_value)/(self.upper_limit-self.initial_value))
            lower_constraint_violation = abs((self.initial_value- value_left)/(self.initial_value-self.lower_limit))
            if upper_constraint_violation >= 1:
                self.current_penalty += self.penalty_value + (upper_constraint_violation - 1)  * robot.priorities[self.priority_value]
        elif boundary == "lower":
            lower_constraint_violation = abs((self.initial_value- value_left)/(self.initial_value-self.lower_limit))
            if lower_constraint_violation >= 1:
                self.current_penalty += self.penalty_value + (lower_constraint_violation - 1)  * robot.priorities[self.priority_value]
        
        return True

    