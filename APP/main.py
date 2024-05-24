from BFS import BFS
from PQ import PQ
from plan import Plan
from task import Task
from robot import Robot
from resource import Resource
from interdependencyConstraint import InterdependencyConstraint
from linearConstraint import LinearConstraint
from map import Map
import pytmx,pygame


starting_position = [19,0]
ending_position = [19,6]
battery = Resource('battery', 100) # battery 
time= Resource('time', 0) # time
hammer = Resource('hammer', -1) # hammer
bolt = Resource('bolt', 1) # one time use 
example_robot = Robot([battery, time, hammer], 1, {
"0": 'infinite',
"1": 10,
"2": 5,
"3": 2,
"4": 1 })
example_task_1 = Task('pick up bolts',{'time': -10, 'hammer': 1, 'battery': 5}, {'bolt': 6}, 200, True, [19,1])
example_task_2 = Task('fix computer',{'time': -10, 'hammer': 1, 'battery': 5, 'bolt':3}, {}, 200, True, [19,2])
example_task_3 = Task('fix motor',{'time': -10, 'hammer': 1, 'battery': 10, 'bolt':2}, {}, 200, True, [19,3])
example_task_4 = Task('complete door repair',{'time': -10, 'hammer': 1, 'battery': 30, 'bolt':1}, {}, 200, True, [19,4])
example_task_5 = Task('close window',{'time': -10}, {}, 200, True, [19,5])
tasks = [example_task_1,example_task_2,example_task_3,example_task_4,example_task_5]
example_constraint_1 = LinearConstraint('time should not go surpass 90','time', 0, None, 90, 100, '2')
example_constraint_2 = InterdependencyConstraint('task 4 needs to be done before task 5',example_task_5, [example_task_4], 1000, '0')
constraints = {
    "discrete": [],
    "linear": [example_constraint_1],
    "interdependency":[ example_constraint_2]}
print("all objects created")
tmx_data = ''
pygame.init()
pygame.display.set_mode((800, 600))
tmx_data = pytmx.load_pygame('example_files/presentation_1.tmx')

example_map = Map(
    starting_position,
    tasks,
    ending_position,
    'example_files/example_map.tmx',
    tmx_data)
example_map.create_graph()
graph = example_map.graph
algorithm = BFS(graph, starting_position, ending_position, tasks, constraints, example_robot)
algorithm.find_solution_plans()
for plan in algorithm.final_plans:
    print("------------------")
    print("path is " + str(plan.path))
    print("value/cost is " + str(plan.value - plan.cost))
    print("distance is "+ str(plan.distance_traveled))
    print("time elapsed is " + str(plan.time_spent))
    for constraint_violated in plan.constraint_penalties:
        #limit = constraint.
        print(
            str(constraint_violated) 
            + " has a penalty of " 
            + str(plan.constraint_penalties[constraint_violated][0])
            )



def load_tmx(filename):
        """Load TMX file."""
        pygame.init()
        pygame.display.set_mode((800, 600))
        tmx_data = pytmx.load_pygame(filename)
        return tmx_data  