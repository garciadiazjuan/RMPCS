class InterdependencyConstraint:
    def __init__(self, name, task, required_tasks, penalty, priority_value):
        self.name = name
        self.task = task
        self.required_tasks = required_tasks
        self.penalty = penalty
        self.priority_value = priority_value
        self.current_penalty = 0

    def check_constraint(self, plan, robot):
        for task in self.required_tasks:
            if task in plan.pending_tasks and self.priority_value == '0':
                return False
        return True

    def update_penalty(self,plan,robot):
        # select which boundary is broken, then use coefficient and priorities to calculate penalty
        for task in self.required_tasks:
            if task in plan.pending_tasks:
                self.current_penalty = self.penalty
        return True