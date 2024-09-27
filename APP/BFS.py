from collections import deque
from PQ import PQ
from plan import Plan
from task import Task
from robot import Robot
from resource import Resource
from interdependencyConstraint import InterdependencyConstraint
from linearConstraint import LinearConstraint

class BFS:
    def __init__(self, graph, initial_position, end_position, tasks, constraints, robot):
        self.graph = graph # dict of directed edges {ABCD: distance} from [A,B] to [C,D] with a cost of distance (INT)
        self.initial_position = initial_position # [A,B] coordinates of initial position
        self.end_position = end_position # [A,B] coordinates or -1 if no final position is necessary
        self.plans = []
        self.final_plans = []
        self.tasks = tasks # all tasks in the problem domain
        self.constraints = constraints # all constraints in the problem domain
        self._queue = PQ()
        self.robot = robot


    def find_solution_plans(self):
        task_schedule_string = "start at " + str(self.initial_position)
        first_plan = Plan([self.initial_position], self.robot, 0, 0, self.tasks, 0, 0, [task_schedule_string])
        self._queue.push(first_plan,0)  # Start with initial position and path
        while not self._queue.is_empty():
            plan = self._queue.pop() # get best next step
            path = plan.path # get path of plan
            pending_tasks = plan.pending_tasks # list of pending tasks
            # If all tasks are done and (robot is in final position / no final position needed)
            if len(plan.pending_tasks) == 0:
                plan.plan_finish(0,self.end_position, self.graph, self.tasks, self.constraints)
            if len(pending_tasks) == 0 and (path[-1] == self.end_position or self.end_position == -1 ):
                self.final_plans.append(plan)
            
            for possible_next_step in plan.calculate_available_moves(self.graph, self.constraints , self.end_position):
                self._queue.push(possible_next_step, possible_next_step.value - possible_next_step.cost)

                
        
        #self.final_plans.sort(key=lambda x: sum(self.graph[x[i]][x[i+1]] for i in range(len(x)-1)))  # Sort plans by total distance
