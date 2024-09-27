import copy
from resource import Resource
class Plan:
    def __init__(self,  path, robot, value, cost, tasks, distance_traveled, time_spent, task_schedule):
        self.path = path # path followed by the plan
        self.robot = robot # robot object associated to plan (has resources and propierties)
        self.value = value # value obtained in the plan
        self.cost = cost # negative cost associated to the plan
        self.pending_tasks= tasks # tasks that have not been done in this plan
        self.distance_traveled = distance_traveled # distance in units traveled by the robot
        self.time_spent = time_spent # time spent so far in units
        self.constraint_penalties = {} # dict of constraints and the penalties endured by the plan
        self.val_cost = 0
        self.task_schedule = task_schedule

    def calculate_available_moves(self, graph, constraints, final_pos):
        # check which tasks need to be done and can be done (items/resources)
        plans = []
        for task in self.pending_tasks:
            copy_tasks = copy.copy(self.pending_tasks)
            a, b = self.path[-1]
            c, d = task.location
            key = ((a, b), (c, d))
            info = graph[key]
            distance = info[1]
            travel_time = distance / self.robot.speed 
            if task.check_if_doable(constraints, self, graph, travel_time):
                new_plan = Plan(
                    copy.copy(self.path), 
                    copy.deepcopy(self.robot), 
                    copy.copy(self.value), 
                    copy.copy(self.cost), 
                    copy_tasks ,
                    copy.copy(self.distance_traveled),
                    copy.copy(self.time_spent),
                    copy.copy(self.task_schedule))
                new_plan.update_plan(constraints, new_plan, task, travel_time)
                # update distance
                # Create the key tuple
                a, b = self.path[-1]
                c, d = task.location
                key = ((a, b), (c, d))
                info = graph[key]
                distance = info[1]
                new_plan.distance_traveled += distance
                plans.append(new_plan)
                

        return plans
    
    def update_plan(self, constraints, new_plan, task, travel_time):
        new_plan.cost = 0
        new_plan.value = new_plan.value + task.value
        new_plan.pending_tasks.remove(task)
        new_plan.path.append(task.location)
        new_plan.task_schedule.append(task.name + " at " + str(task.location))
        # update every penalty val
        for constraint_type in constraints:
            if constraint_type == "interdependency":
                    for constraint in constraints[constraint_type]:
                        if constraint.task == task:
                            constraint.update_penalty(new_plan,new_plan.robot)
                            new_plan.cost += constraint.current_penalty
            else:   
                for constraint in constraints[constraint_type]:
                    constraint.update_penalty(new_plan,new_plan.robot)
                    new_plan.cost += constraint.current_penalty

        # update resources consumed
        robot_resources = {}
        for resource in new_plan.robot.resources:
            robot_resources[resource.name] = resource.value_left
        for resource_consumed in task.resource_consumes: # for every item that the task consumes
            if robot_resources[resource_consumed] != -1: # if that resource is not infinitely usable
                for resource in new_plan.robot.resources:
                    if resource.name == resource_consumed:
                        resource.value_left -= task.resource_consumes[resource_consumed]
        
        # update resources obtained
        robot_resources = {}
        for resource in new_plan.robot.resources:
            robot_resources[resource.name] = resource.value_left
        for resource_obtained in task.resource_gives: # for every item that the task consumes
            if resource_obtained in robot_resources: # if robot already has of that resource
                if robot_resources[resource_obtained] != -1: # if that resource is not infinitely usable
                    for resource in new_plan.robot.resources:
                        if resource.name == resource_consumed:
                            resource.value_left += task.resource_gives[resource_obtained]
            else:
                new_resource = Resource(resource_obtained, task.resource_gives[resource_obtained])
                new_plan.robot.resources.append(new_resource)
        robot_resources = {}
        for resource in new_plan.robot.resources:
            robot_resources[resource.name] = resource.value_left
        
        return True
    def plan_finish(self, distance, final_pos, graph, tasks, constraints):
        self.path.append(final_pos) # append final pos
        final_task_string = "end at " + str(final_pos)
        self.task_schedule.append(final_task_string)

        # update time and distance      
        self.val_cost = self.value
        a, b = self.path[-2]
        c, d = final_pos
        key = ((a, b), (c, d))
        info = graph[key]
        distance = info[1]
        self.distance_traveled += distance
        self.time_spent = self.distance_traveled / self.robot.speed
        for resource in self.robot.resources:
            # if robot has a resource with name time get it
            if resource.name == "time":
                self.time_spent += resource.value_left
                resource.value_left = self.time_spent
            # else get time from distance traveled divided by robot speed


        self.cost = 0
        # update every penalty val
        for constraint_type in constraints:
            if constraint_type == "interdependency":
                    for constraint in constraints[constraint_type]:
                        constraint.update_penalty(self,self.robot)
                        self.constraint_penalties[constraint.name] = [constraint.current_penalty]
                        self.cost += constraint.current_penalty
                        
            else:   
                for constraint in constraints[constraint_type]:
                    constraint.update_penalty(self,self.robot)
                    self.constraint_penalties[constraint.name] = [constraint.current_penalty,constraint.upper_limit, constraint.lower_limit]
                    self.cost += constraint.current_penalty
        self.val_cost -= self.cost
