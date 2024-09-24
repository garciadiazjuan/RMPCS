from cProfile import label
import os
from pickle import TUPLE
import tempfile
from unicodedata import name
from urllib.request import pathname2url
import zipfile
from importlib_metadata import distribution
import numpy as np
import datetime as dt
import dash
import dash_leaflet as dl
from dash import dcc, ctx
from dash import html
import pytmx
import pygame
import pandas as pd
import plotly.graph_objects as go
import scipy.stats as stats
import scipy.special as KL
import csv
import random
import base64
import io
import json
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from zipfile import ZipFile
from ast import literal_eval
import PIL.Image as PILImage
import xml.etree.ElementTree as ET
import time as t

import linearConstraint as LC
import interdependencyConstraint as IC
import resource as Resource
import task as task
from BFS import BFS
from PQ import PQ
from plan import Plan
from robot import Robot
from map import Map

from simulation import run_love2d_project, create_simulation_csv, create_simulation_txt

###################   VARIABLE DECLARATIONS   #########################################################################################

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

app.title = "RMPCS"
server = app.server


files = dict()
uploaded_files = {}
fileNR = 0



battery = Resource.Resource('battery', 100) # battery 
time= Resource.Resource('time', 0) # time
hammer = Resource.Resource('hammer', 100) # hammer
bolt = Resource.Resource('bolt', 1) # one time use 

resources = list()
resources.append(battery)
resources.append(time)
resources.append(hammer)
resources.append(bolt)

example_robot = Robot([battery, time, hammer], 1, {
"0": 'infinite',
"1": 10,
"2": 5,
"3": 2,
"4": 1 })


tasks = list()
example_task_1 = task.Task('pick up bolts',{'time': -4, 'hammer': 1, 'battery': 5}, {'bolt': 6}, 200, True, [19,3])
example_task_2 = task.Task('fix computer',{'time': -2, 'hammer': 1, 'battery': 5, 'bolt':3}, {}, 200, True, [19,7])
example_task_3 = task.Task('fix conveyor belt',{'time': -7, 'hammer': 1, 'battery': 10, 'bolt':2}, {}, 200, True, [16,7])
example_task_4 = task.Task('complete door repair',{'time': -3, 'hammer': 1, 'battery': 30, 'bolt':1}, {}, 200, True, [16,7])
example_task_5 = task.Task('open package',{'time': -8}, {}, 200, True, [16,9])
tasks.append(example_task_1)
tasks.append(example_task_2)
tasks.append(example_task_3)
tasks.append(example_task_4)
tasks.append(example_task_5)


constraints = list()
idconstraints = list()
example_constraint_1 = LC.LinearConstraint('time should not surpass 90','time', 0, None, 90, 100, '2')
example_constraint_2 = IC.InterdependencyConstraint('task 4 needs to be done before task 5',example_task_5, [example_task_4], 1000, '0')

constraints.append(example_constraint_1)
idconstraints.append(example_constraint_2)

map_data =[]
graph = list()

encoded_image = None

simulation_final_plan = 0
simulation_graph = {}
simulation_robot_speed = 0
simulation_tasks = tasks

###################   RENDER MAP   ###########################################################################

def load_tmx(filename):
    """Load TMX file."""
    tmx_data = pytmx.load_pygame(filename)
    return tmx_data

def render_tmx(tmx_data):
    """Render TMX map."""
    map_surface = pygame.Surface((tmx_data.width * tmx_data.tilewidth, tmx_data.height * tmx_data.tileheight))
    for layer in tmx_data.visible_layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                tile = tmx_data.get_tile_image_by_gid(gid)
                if tile:
                    tile.set_alpha(254)  # Example: Set alpha for transparency
                    map_surface.blit(tile, (x * tmx_data.tilewidth, y * tmx_data.tileheight))
    return map_surface

def save_as_png(surface, filename):
    """Save surface as PNG file."""
    pygame.image.save(surface, filename)

def create_map_structure(tmx_data):
    for row in range(tmx_data.height):
        row = []
        for column in range(tmx_data.width):
            row.append(0)
        map_data.append(row)
    return map_data

def generate_map():
    # Initialize pygame
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.HIDDEN)

    # load tmx file
    tmx_filename = "./example_files/presentation_1.tmx"
    tmx_data = load_tmx(tmx_filename)

    # Render TMX map
    map_surface = render_tmx(tmx_data)

    # Save rendered map as PNG
    save_as_png(map_surface, "./example_files/rendered_map.png")

    # create map structure
    map_data = create_map_structure(tmx_data)

    # Define map image
    image_filename = './example_files/rendered_map.png'
    encoded_image = base64.b64encode(open(image_filename, 'rb').read())

    pygame.quit()

    return tmx_data, map_data, encoded_image

tmx_data, map_data, encoded_image = generate_map()

###################   HTML BLOCKS   #######################################################################################


# HTML block of the header

header_left = html.Div(
    [
        html.H4("RMPCS", className="app__header__title"),
        html.P("",className="app__header__title--green")
    ],
    className="app__header__desc"
)

header_right = html.Div(
    [
        html.A(
            html.Button("SOURCE CODE", className="link-button"),
            href=""
        ),
        html.A(
            html.Button("APP description", className="link-button"),
            href=""
        )
    ],
    className="app__header__logo"
)


# HTML block for the map

map_box_inner = [
    html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()),
            style={'width': '100%', 'height': 'auto'}),

    html.Div(
        id='grid-container',
        children=[
            html.Div(
                id=f'tile-{i}-{j}',
                className='grid-tile',
                style={
                    'position': 'absolute',
                    'left': f'{j * 100 / len(map_data[0])}%',
                    'top': f'{i * 100 / len(map_data)}%',
                    'width': f'{100 / len(map_data[0])}%',
                    'height': f'{100 / len(map_data)}%',
                    'border': '1px solid black',
                    'background-color': 'rgba(0, 0, 0, 0.1)',
                    'font-size': '12px'
                },
                children = (
                    [
                        html.H6(
                            f"{i},{j}", style={ 'color': 'black', 'font-size': '12px'},
                        )
                    ]
                )
            )
            for i in range(len(map_data))
            for j in range(len(map_data[0]))
        ]
    )
]

map_box = html.Div(id='map-container', style={'position': 'relative', 'width': '100%', 'max-width': '800px', 'margin': '0 auto'}, 
    children=map_box_inner,
    className="create__and__evaluate__container third"
)


# HTML block to show or hide the grid

hide_grid_box = html.Div(
    [
        dcc.Dropdown(
            id = 'dropdown-to-show_or_hide-grid',
            options=[
                {'label': 'Hide grid', 'value': 'off'},
                {'label': 'Show grid', 'value': 'on'}
            ],
            value = 'off'
        ),
    ],
    className="create__and__evaluate__container second"
)


# HTML block for the upload of the map file

upload_box = html.Div(
    [
        html.H6("UPLOAD MAP FILE", className="container__title"),
        html.Div(
            [
                dcc.Upload(
                    id="upload-data",
                    children=html.Div(
                        ["Drag and drop or click to select a file to upload."]
                    ),
                    style={
                        "width": "95%",
                        "height": "60px",
                        "lineHeight": "60px",
                        "borderWidth": "1px",
                        "borderStyle": "dashed",
                        "borderRadius": "5px",
                        "textAlign": "center",
                        "margin": "10px",
                    },
                    multiple=True,
                ),
                html.Div(id="uploaded-file"),
            ],
            style={"padding-bottom": "1em"},
        ),
    ],
    className="create__and__evaluate__container second",
)


# HTML block to show, add and edit resources

input_resources = html.Div(
    [
        dbc.InputGroup(
            [dbc.InputGroupText("Resource"), dbc.Input(id="resource-name",placeholder="Specify the resource here")],
            className="mb-3", size="lg"
        ),
        dbc.InputGroup(
            [
                dbc.InputGroupText("Uses"),
                dbc.Input(id="resource-value", placeholder="Specify how much of the resource is available", type="number"),
            ],
            className="mb-3",
        )
    ]
)

resource_box = html.Div(
    [   
        html.H6("RESOURCES", className="container__title"),
        dbc.ListGroup(
            children = [
                dbc.ListGroupItem(f"{resources[i].name} starting with {resources[i].value_left} units")
                for i in range(len(resources))
            ], id="resource-list"
        ),
        html.H6("ADD RESOURCE", className="container__title"),
        input_resources,
        html.A(
            html.Button("Add Resource", className="evaluate-button", id="add-resource-button")
        ),
        dcc.ConfirmDialog(id="resource-creation", message="Distribution successfully added to list")
    ],
    className="create__and__evaluate__container first"
)


# HTML block to show, add and edit tasks

input_tasks = html.Div(
    [
        dbc.InputGroup(
            [
                dbc.InputGroupText("Name"),
                dbc.Input(id="task-name", placeholder="Enter a name for the task")
            ],
            className="mb-3",
        ),
        dbc.InputGroup(
            [
                dbc.InputGroupText("Location"),
                dbc.InputGroupText("X"), 
                dbc.Input(id="x_location", placeholder="x"),
                dbc.InputGroupText("Y"),
                dbc.Input(id="y_location", placeholder="y")],
            className="mb-3", size="lg"
        ),
        dbc.InputGroup(
            [
                dbc.InputGroupText("Value"),
                dbc.Input(id="task_value", placeholder="Enter number between 1 and 100", type="number")
            ],
            className="mb-3",
        ),
        dbc.InputGroup(
            [
                dbc.InputGroupText("Gives resource"),
                dbc.Select(
                    options=[
                        {"label": f"{resources[i].name}", "value": f"{resources[i].name}"}
                        for i in range(len(resources))
                    ], id="gives-resource"
                )
            ]
        ),
        dbc.InputGroup(
            [
                dbc.InputGroupText("Consumes resource"),
                dbc.Select(
                    options=[
                        {"label": f"{resources[i].name}", "value": f"{resources[i].name}"}
                        for i in range(len(resources))
                    ], id="requires-resource"
                ),
            ]
        ),
    ]
)

task_box = html.Div(
    [
        html.H6("TASKS", className="container__title"),
        dbc.ListGroup(
            children = [
                dbc.ListGroupItem(f"{tasks[i].name} at [{tasks[i].location[0]},{tasks[i].location[1]}] value = {tasks[i].value} gives: "
                                + ", ".join(f"{tasks[i].resource_gives[resource]}x {resource}" for resource in tasks[i].resource_gives)
                                +f" requires: "
                                + ", ".join(f"{tasks[i].resource_consumes[resource]}x {resource}" for resource in tasks[i].resource_consumes))
                for i in range(len(tasks))
            ], id="task-list"
        ),
        html.H6("Add Task", className="container__title"),
        input_tasks,
        html.A(html.Button("Add task", className="evaluate-button", id="add-task-button")),
    ],
    className="create__and__evaluate__container first",
)


# HTML block sho show, add and edit constraints

input_linear_constraints = html.Div(
    [
        dbc.InputGroup(
            [
                dbc.InputGroupText("Constrained Recourse"),
                dbc.Select(
                    options=[
                        {"label": f"{resources[i].name}", "value": resources[i].value_left}
                        for i in range(len(resources))
                    ], id="constrained-resource"
                )
            ]
        ),
        dbc.InputGroup(
            [dbc.InputGroupText("Upper Limit"), dbc.Input(id='upper-limit', placeholder="Specify a number higher than the initial value", type="number")],
            className="mb-3",
        ),
        dbc.InputGroup(
            [dbc.InputGroupText("Lower Limit"), dbc.Input(id='lower-limit', placeholder="Specify a number lower than the initial value", type="number")],
            className="mb-3",
        ),
        dbc.InputGroup(
            [dbc.InputGroupText("Priority"), dbc.Input(id='constraint-priority', placeholder="Specify a number between 0 and 1000", type="number")],
            className="mb-3",
        ),
        dbc.InputGroup(
            [
                dbc.InputGroupText("Penalty growth"),
                dbc.Select(
                    options=[
                        {"label": "1 - infinite penalty growth", "value": 0},
                        {"label": "2 - times 10 penalty growth", "value": 1},
                        {"label": "3 - times 6 penalty growth", "value": 2},
                        {"label": "4 - times 3 penalty growth", "value": 3},
                        {"label": "5 - times 1 penalty growth", "value": 4},
                    ], id='penalty-growth'
                ),
            ]
        ),
    ]
)

input_interdependency_constraints = html.Div(
    [
        dbc.InputGroup(
            [dbc.InputGroupText("Name"), dbc.Input(id="idc-name", placeholder="Name this constraint")],
            className="mb-3",
        ),
        dbc.InputGroup(
            [
                dbc.InputGroupText("Constrained Task"),
                dbc.Select(
                    options=[
                        {"label": f"Task at location {tasks[i].location} with value {tasks[i].value}", "value": i}
                        for i in range(len(tasks))
                    ], id="constrained-task"
                )
            ]
        ),
        dbc.InputGroup(
            [
                dbc.InputGroupText("Required Tasks"),
                dcc.Checklist(
                    options=[
                        {'label': f" Task at {tasks[i].location} with value {tasks[i].value}", 'value': i}
                        for i in range(len(tasks))
                    ],id='task-dependencies'
                )
            ]
        ),
        dbc.InputGroup(
            [
                dbc.InputGroupText("Penalty value"),
                dbc.Input(id="idc-penalty", placeholder="Enter a priority value between 0 and 1000", type="number")
            ],
            className="mb-3",
        ),
        dbc.InputGroup(
            [
                dbc.InputGroupText("Constraint type"),
                dbc.Select(
                    options=[
                        {"label": "0 - hard constraint", "value": 0},
                        {"label": "1 - soft constraint", "value": 1},
                    ], id='idc-type'
                )
            ]
        ),
    ]
)

constraint_box = html.Div(
    [
        html.H6("CONSTRAINTS", className="container__title"),
        dbc.ListGroup(
            children = [
                dbc.ListGroupItem(f"{constraints[i].resource}: upper limit {constraints[i].upper_limit}, lower limit {constraints[i].lower_limit}, initial value {constraints[i].initial_value}, penalty {constraints[i].penalty_value}, priority {constraints[i].priority_value} ")
                for i in range(len(constraints))
            ], id='constraint-list'
        ),
        html.H6("Add Linear Constraint", className="container__title"),
        input_linear_constraints,
        html.A(html.Button("Add constraint", className="evaluate-button", id="add-constraint-button")),
        dcc.ConfirmDialog(
            id='constraint-creation-output',
            message='Constraint creation unsuccessful. Make sure to include all values and that the upper and lower level is higher/lower than the initial value.',
        ),
    ],
    className="create__and__evaluate__container first",
)

idconstraint_box = html.Div(
    [
        html.H6("TASK INTERDEPENDENCIES", className="container__title"),
        dbc.ListGroup(
            children = [
                dbc.ListGroupItem(
                    f"{idconstraint.name}: Task {idconstraint.task.name} depends on "
                    + ", ".join(task.name for task in idconstraint.required_tasks) 
                    + f" and would receive a penalty of {idconstraint.penalty}, constraint type {idconstraint.priority_value}"
                )
                for idconstraint in idconstraints
            ], id='idconstraint-list'
        ),
        html.H6("Add Task Interdependency", className="container__title"),
        input_interdependency_constraints,
        html.A(html.Button("Add Task Interdependency", className="evaluate-button", id="add-idc-button")),
        dcc.ConfirmDialog(
            id='idc-creation-output',
            message='Constraint creation unsuccessful. Make sure to include all required fields.',
        ),
    ],
    className="create__and__evaluate__container first",
)

# HTML block to show the generated plan

show_plan_box = html.Div(
    [
        html.H6("PLAN", className="container__title"),
        html.A(html.Button("Generate a plan", className="evaluate-button", id="plan-button")),
        dcc.ConfirmDialog(
            id='plan-output',
            message='Plan created',
        ),
        dbc.Progress(id='plan_value', value=0),
        html.H6("Path", className="container__title"),
        html.H6("Distance and Time", className="container__title"),
        html.H6("Constraints", className="container__title"),
        html.A(html.Button("Start Execution", className="evaluate-button", id="start-execution-button")),
        dcc.ConfirmDialog(
            id='execution-output',
            message='Replanning needed',
        ),
    ],
    className="create__and__evaluate__container second"
)


###################   LAYOUT   #########################################################################################


app.layout = html.Div(
    [
        # header
        html.Div(
            [
                header_left,
                header_right,
            ],
            className="app__header",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.H6("MAP", className="container__title"),
                                map_box,
                                hide_grid_box,
                                upload_box,
                            ],
                            className="create__and__evaluate__container first"
                        )
                    ],
                    className="two-thirds column left_column",
                ),
                html.Div(
                    [
                        resource_box,
                        task_box,
                    ],
                    className="one-third column right__column",
                ),
            ],
            className="app__content",
        ),
        html.Div(
            [
                html.Div(
                    [
                        constraint_box,
                    ],
                    className="column left_column"
                ),
                html.Div(
                    [
                        idconstraint_box,
                    ],
                    className="column right_column"
                )
            ],
            className="app__content",
        ),
        html.Div(
            [
                html.Div(
                    [
                        show_plan_box,
                    ],
                    id="plan-box",
                    className="column"
                ),
            ],
            className="app__content",
        ),
        dcc.Interval(
            id='interval-component',
            interval=2000,  # Interval in milliseconds (2000 ms = 2 seconds)
            n_intervals=0  # Start counting intervals from 0
        ),
    ],
    className="app__container",
)


###################   CALLBACKS   #########################################################################################

@app.callback(
    Output("map-container", "children"),
    [Input("upload-data", "filename"), 
    Input("upload-data", "contents")],
    prevent_initial_call=True
)
def update_output(uploaded_filenames, uploaded_file_contents):
    """saves files individually when uploaded to server

    Args:
        uploaded_filenames (String): filenames
        uploaded_file_contents (File): content of files

    Returns:
        empty string: the return function call is used to save the files
    """
    if len(uploaded_filenames)==2 and uploaded_file_contents is not None:
        with open(os.path.join('assets', uploaded_filenames[0]), 'wb') as f:
            f.write(uploaded_file_contents[0])
        with open(os.path.join('assets', uploaded_filenames[1]), 'wb') as f:
            f.write(uploaded_file_contents[1])
        map_box, encoded_image = generate_map()
        return [
            html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()),
                    style={'width': '100%', 'height': 'auto'}),

            html.Div(
                id='grid-container',
                children=[
                    html.Div(
                        id=f'tile-{i}-{j}',
                        className='grid-tile',
                        style={
                            'position': 'absolute',
                            'left': f'{j * 100 / len(map_data[0])}%',
                            'top': f'{i * 100 / len(map_data)}%',
                            'width': f'{100 / len(map_data[0])}%',
                            'height': f'{100 / len(map_data)}%',
                            'border': '1px solid black',
                            'background-color': 'rgba(0, 0, 0, 0.1)',
                            'font-size': '12px'
                        },
                        children = (
                            [
                                html.H6(
                                    f"{i},{j}", style={ 'color': 'black', 'font-size': '12px'},
                                )
                            ]
                        )
                    )
                    for i in range(len(map_data))
                    for j in range(len(map_data[0]))
                ]
            )
        ]
    else:
        return map_box_inner


@app.callback(
    Output('grid-container', 'children'),
    Input('dropdown-to-show_or_hide-grid', 'value'))
def show_grid(visibility):
    if visibility =='on':
        return [
            html.Div(
                id=f'tile-{i}-{j}',
                className='grid-tile',
                style={
                    'position': 'absolute',
                    'left': f'{j * 100 / len(map_data[0])}%',
                    'top': f'{i * 100 / len(map_data)}%',
                    'width': f'{100 / len(map_data[0])}%',
                    'height': f'{100 / len(map_data)}%',
                    'border': '1px solid black',
                    'background-color': 'rgba(0, 0, 0, 0.1)'
                },
                children = (
                    [
                        html.H6(
                            f"{i},{j}", style={ 'color': 'black', 'size': '0.5em', 'line-height': '0.7'},
                        )
                    ]
                )
            )
            for i in range(len(map_data))
            for j in range(len(map_data[0]))
        ]
    else:
        return html.H6(
                    f"no display", style={ 'display': 'none'},
                ),


@app.callback(Output('resource-list', 'children'),
              Input('add-resource-button', 'n_clicks'),
              State('resource-name', 'value'),
              State('resource-value', 'value'))
def add_resource(notUsed, name, value):
    if not(name == None) and not(value==None):
        new_resource = resource.Resource(name, value)
        resources.append(new_resource)

    resource_list = [
            dbc.ListGroupItem(f"Resource {resources[i].name} with {resources[i].value_left} uses")
            for i in range(len(resources))
        ]
    return resource_list

   
@app.callback(Output('task-list', 'children'),
            Input('add-task-button', 'n_clicks'),
            State('task-name', 'value'),
            State('x_location', 'value'),
            State('y_location', 'value'),
            State('task_value', 'value'),
            State('gives-resource', 'value'),
            State('requires-resource', 'value'))
def add_task(notUsed, name, x, y, value, gives, requires):
    if not(x == None or y==None or value==None):
        location=[x,y]
        new_task = task.Task(name, requires, gives, value, True, location)
        tasks.append(new_task)
        
    task_list = [
        dbc.ListGroupItem(f"{tasks[i].name} at [{tasks[i].location[0]},{tasks[i].location[1]}] value = {tasks[i].value} gives: "
                        + ", ".join(f"{tasks[i].resource_gives[resource]}x {resource}" for resource in tasks[i].resource_gives)
                        +f" requires: "
                        + ", ".join(f"{tasks[i].resource_consumes[resource]}x {resource}" for resource in tasks[i].resource_consumes))
        for i in range(len(tasks))
    ]
    return task_list


@app.callback(Output('constraint-list', 'children'),
            Output('constraint-creation-output', 'displayed'), 
            Input('add-constraint-button', 'n_clicks'),
            State('constrained-resource', 'label'),
            State('constrained-resource', 'value'),
            State('upper-limit', 'value'),
            State('lower-limit', 'value'),
            State('constraint-priority', 'value'),
            State('penalty-growth', 'value'),
            prevent_initial_call = True)
def add_constraint(notUsed, resource_name, resource_value, upper, lower, priority, growth):
    constraint_list = [
        dbc.ListGroupItem(f"{constraints[i].resource}: upper limit {constraints[i].upper_limit}, lower limit {constraints[i].lower_limit}, initial value {constraints[i].initial_value}, penalty {constraints[i].penalty_value}, priority {constraints[i].priority_value} ")
        for i in range(len(constraints))
    ]
    if not(resource_name == None or priority==None or growth==None):
        if not(0<=priority<=1000):
            return constraint_list, True
        resource_value = int(resource_value)
        if upper==None:
            if not(lower==None):
                if lower < resource_value:
                    new_constraint = LC.LinearConstraint(resource_name, resource_value, None, lower, priority, growth)
                    constraints.append(new_constraint)
                else:
                    return constraint_list, True
            else: return constraint_list, True
        else:
            if upper > resource_value:
                if not(lower==None):
                    if lower < resource_value:
                        new_constraint = LC.LinearConstraint(resource_name, resource_value, upper, lower, priority, growth)
                        constraints.append(new_constraint)
                    else:
                        return constraint_list, True
                else:
                    new_constraint = LC.LinearConstraint(resource_name, resource_value, upper, None, priority, growth)
                    constraints.append(new_constraint)
            else:
                return constraint_list, True
        
    constraint_list = [
        dbc.ListGroupItem(f"{constraints[i].resource}: upper limit {constraints[i].upper_limit}, lower limit {constraints[i].lower_limit}, initial value {constraints[i].initial_value}, penalty {constraints[i].penalty_value}, priority {constraints[i].priority_value} ")
        for i in range(len(constraints))
    ]
    return constraint_list, False


@app.callback(Output('idconstraint-list', 'children'),
            Output('idc-creation-output', 'displayed'), 
            Input('add-idc-button', 'n_clicks'),
            State('idc-name', 'value'),
            State('constrained-task', 'value'),
            State('task-dependencies', 'value'),
            State('idc-penalty', 'value'),
            State('idc-type', 'value'),
            prevent_initial_call = True)
def add_idconstraint(notUsed, name, task, dependencies, penalty, type):
    constraint_list = [
        dbc.ListGroupItem(
            f"{idconstraint.name}: Task {idconstraint.task.name} depends on "
            + ", ".join(task.name for task in idconstraint.required_tasks) 
            + f" and would receive a penalty of {idconstraint.penalty}, constraint type {idconstraint.priority_value}"
        )
        for idconstraint in idconstraints
    ]
    if not(task == None or len(dependencies)==0 or penalty==None or type==None):
        if not(0<=penalty<=1000):
            return constraint_list, True
        
        dependency_list = []
        for i in dependencies:
            new_dep = tasks[i]
            dependency_list.append(new_dep)
        if tasks[int(task)] in dependency_list:
            return constraint_list, True
        
        new_constraint = IC.InterdependencyConstraint(name, tasks[int(task)], dependency_list, penalty, type)
        idconstraints.append(new_constraint)
    else:
        return constraint_list, True
      
    constraint_list = [
        dbc.ListGroupItem(
            f"{idconstraint.name}: Task {idconstraint.task.name} depends on "
            + ", ".join(task.name for task in idconstraint.required_tasks) 
            + f" and would receive a penalty of {idconstraint.penalty}, constraint type {idconstraint.priority_value}"
        )
        for idconstraint in idconstraints
    ]
    return constraint_list, False


@app.callback(Output('plan-box', 'children'), 
            Input('plan-button', 'n_clicks'),
            prevent_initial_call = True)
def plan(n_clicks):
    starting_position = [19,1]
    ending_position = [19,0]
    all_constraints = {
        "discrete": [],
        "linear": constraints,
        "interdependency":idconstraints}
    
    print("all objects created")
    
    example_map = Map(
        starting_position,
        tasks,
        ending_position,
        'example_files/map.tmx',
        tmx_data)
    print('map works')
    example_map.create_graph()
    global graph
    graph = example_map.graph
    for el in graph:
        print(el)
        print(graph[el])
    algorithm = BFS(graph, starting_position, ending_position, tasks, all_constraints, example_robot)
    print('initializing the algorithm works')
    algorithm.find_solution_plans()
    print('running the algorithm works')
    best_plan = algorithm.final_plans[0]
    for plan in algorithm.final_plans:
        if plan.val_cost > best_plan.val_cost:
            best_plan = plan
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
    global simulation_final_plan 
    simulation_final_plan = best_plan
    simulation_graph = graph
    idconstraint_violation = list()
    constraint_violation = list()
    print("constraints cominggggg")
    for i in best_plan.constraint_penalties:
        print(i)
        print(best_plan.constraint_penalties[i])
    #create_simulation_txt(simulation_final_plan, simulation_graph, tasks)

    return html.Div(
        [
            html.H6("PLAN", className="container__title"),
            html.A(html.Button("Generate a plan", className="evaluate-button", id="plan-button")),
            dcc.ConfirmDialog(
                id='plan-output',
                message='Plan created',
            ),
            html.H6("Plan Value", className="container__title"),
            dbc.Progress(
                [
                    dbc.Progress(id='plan_value', value=(best_plan.value-best_plan.cost)/10, label=f'{(best_plan.value-best_plan.cost)/10}%', color="#6AB648", style={"height": "30px", "font-size":"20px"}, bar=True),
                    dbc.Progress(id='plan_value_negative', value=best_plan.cost/10, color="danger", style={"height": "30px"}, bar=True),
                ],
                style={"height": "30px"}
            ),
            html.H6("Path", className="container__title"),
            dbc.ListGroup(
                children = [
                    dbc.ListGroupItem(f"{best_plan.task_schedule[i]} ")
                    for i in range(len(best_plan.task_schedule))
                ], id='constraint-list'
            ),
            html.H6("Distance and Time", className="container__title"),
            dbc.ListGroup(
                children = [
                    dbc.ListGroupItem(f"Distance Traveled: {best_plan.distance_traveled} units"),
                    dbc.ListGroupItem(f"Time Spent: {best_plan.time_spent} seconds"),
                ]
            ),
            html.H6("Constraints", className="container__title"),
            dbc.ListGroup(
                children = [
                    dbc.ListGroupItem(f"The constraint '{i}' has lead to a penalty of {round(best_plan.constraint_penalties[i][0], 2)}")
                    for i in best_plan.constraint_penalties
                ]
            ),
            html.A(html.Button("Start Execution", className="evaluate-button", id="start-execution-button")),
            dcc.ConfirmDialog(
                id='execution-output',
                message='Could not start simulation',
            ),
        ],
        className="create__and__evaluate__container second"
    )


@app.callback(Output('execution-output', 'displayed'),
            Input('start-execution-button', 'n_clicks'),
            prevent_initial_call = True)
def start_execution(n_clicks):
    print("task schedule is " + str(simulation_final_plan.task_schedule))
    print("best path is " + str(simulation_final_plan.path))
    
    moving = True
    performing_task= False
    task_schedule_string = "start at " + str(simulation_final_plan.path[0])
    global tasks
    global resources
    global example_robot
    executed_plan = Plan([simulation_final_plan.path[0]], example_robot, 0, 0, tasks, 0, 0, [task_schedule_string])
    current_position = executed_plan.path[0]
    left_to_move = graph[tuple(simulation_final_plan.path[0]), tuple(simulation_final_plan.path[1])][0]
    print('left to move:')
    print(left_to_move)
    replanning_needed = False
    next_task = 1
    task_time = 0
    # start "timer"
    while(replanning_needed==False):
        # wait one second
        t.sleep(1)
        # if moving update position, time and resources
        if moving == True:
            moving, performing_task, task_time, current_position = move(left_to_move, executed_plan, current_position, moving, performing_task, task_time)
        if performing_task == True:
            performing_task, moving, next_task, task_time, left_to_move, end, replanning_needed = perform_task(next_task, executed_plan, task_time, moving, performing_task, left_to_move, replanning_needed)
            if end==True:
                return True
        executed_plan.time_spent += 1
        #executed_plan.robot.resources['time'] += 1
    tasks = executed_plan.pending_tasks
    resources = executed_plan.robot.resources
    example_robot = executed_plan.robot
    return False

def move(left_to_move, executed_plan, current_position, moving, performing_task, task_time):
    # check if moving finished
    if not left_to_move:
        print('finished moving')
        moving = False
        performing_task = True
        task_time = 0
        executed_plan.path.append(current_position)
        # TODO: randomly decide if replanning is needed
            #replanning_needed = True
    else:
        # update current position and remove the previous one from left to move
        current_position = left_to_move[0]
        left_to_move.remove(current_position)
        print('moving')
    return moving, performing_task, task_time, current_position

def perform_task(next_task, executed_plan, task_time, moving, performing_task, left_to_move, replanning_needed):
    # find current task
    task_string = simulation_final_plan.task_schedule[next_task]
    print(task_string)
    task_name, task_location = task_string.split(" at ")
    current_task = ""
    end = False
    for task in tasks:
        if task.name == task_name:
            if str(task.location) == task_location:
                current_task = task
    # check if task is completed
    if task_time == -current_task.resource_consumes['time']:
        print('finished task')

        for resource in current_task.resource_consumes:
            for robot_resource in executed_plan.robot.resources:
                if robot_resource.name == resource:
                    if (not resource=='time') and (not current_task.resource_consumes[resource]==-1):
                        fluctuation = random.uniform(0.4, 1.6)  # Fluctuate by ±10%
                        adjusted_consumption = current_task.resource_consumes[resource] * fluctuation
                        adjusted_consumption = round(adjusted_consumption)
                        robot_resource.value_left -= adjusted_consumption
                        print(f"{resource} consumed with fluctuation: {adjusted_consumption:.2f}")

                        # Check if deviation is more than 5%
                        if fluctuation < 0.5 or fluctuation > 1.5:
                            print('replanning needed')
                            replanning_needed = True

        for resource in current_task.resource_gives:
            resource_in_robot = False
            for robot_resource in executed_plan.robot.resources:
                if robot_resource.name == resource:
                    resource_in_robot = True
                    if (not resource=='time') and (not current_task.resource_gives[resource]==-1):
                        fluctuation = random.uniform(0.4, 1.6)  # Fluctuate by ±10%
                        adjusted_giving = current_task.resource_gives[resource] * fluctuation
                        adjusted_giving = round(adjusted_giving)
                        robot_resource.value_left += adjusted_giving
                        print(f"{resource} given with fluctuation: {adjusted_giving:.2f}")

                        # Check if deviation is more than 5%
                        if fluctuation < 0.5 or fluctuation > 1.5:
                            print('replanning needed')
                            replanning_needed = True
            if resource_in_robot == False:
                executed_plan.robot.resources.append(Resource.Resource(resource, current_task.resource_gives[resource]))
        # update tasks
        if executed_plan.pending_tasks:
            executed_plan.pending_tasks.remove(current_task)

        # prepare for moving
        performing_task = False
        moving = True
        next_task += 1
        # print(left_to_move)
        if not len(simulation_final_plan.path) == next_task+1:
            left_to_move = graph[tuple(simulation_final_plan.path[next_task-1]), tuple(simulation_final_plan.path[next_task])][0]
        else: 
            print('all tasks executed')
            for resource in executed_plan.robot.resources:
                print(resource.name)
                print(resource.value_left)
            print(executed_plan.pending_tasks)
            end = True


    task_time += 1
    return performing_task, moving, next_task, task_time, left_to_move, end, replanning_needed


# Callback that is triggered by the interval
@app.callback(
    Output('output', 'children'),
    Input('interval-component', 'n_intervals')  # Trigger every 2 seconds
)
def update_output(n_intervals):
    # randomly update resources (optional)
    random = np.random()

    # check if new planning is needed
    if(random == 1):
        # replanning
        print('replanning')
    elif(random == 0):
        # no replanning
        print('no replanning')

    return f"Interval triggered {n_intervals} times"
###################   MAIN   #########################################################################################


if __name__ == "__main__":
    app.run_server(debug=False,dev_tools_ui=False,dev_tools_props_check=False)
