import subprocess
import os
import sys
import csv

def run_love2d_project():
    current_directory = os.path.dirname(__file__)
    current_directory = current_directory[:-3]
    print(current_directory)
    project_path = os.path.join(current_directory,'LuaSimulator/')
    if not os.path.isdir(project_path):
        print(f"Project path {project_path} does not exist.")
        sys.exit(1)
    # Determine the command to run based on the operating system
    if sys.platform.startswith('win'):
        love_command = 'love.exe'
    elif sys.platform.startswith('darwin'):
        love_command = '/Applications/love.app/Contents/MacOS/love'
    else:
        love_command = 'love'

    # Run the LÖVE2D project
    try:
        subprocess.run([love_command, project_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running LÖVE2D project: {e}")

def create_simulation_csv(best_plan, graph, tasks):
    current_directory = os.path.dirname(__file__)
    current_directory = current_directory[:-3]
    csv_path = os.path.join(current_directory,'LuaSimulator/simulator_data.csv')
    #open csv at a specific location
    with open(csv_path, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        # append first element to csv (last stop)
        last_stop = best_plan.path[0]
        csvfile.write(''.join([ str(last_stop[0]),'/',str(last_stop[1])]) + ',')
        for stop in best_plan.path[1:]:
            a, b = last_stop
            c, d = stop
            key = ((a, b), (c, d))
            path_tiles = graph[key][0]
            # for each tile in graph
            for tile in path_tiles[1:]:
                # append tile to csv (last_stop)
                last_stop = tile
                csvfile.write(''.join([ str(last_stop[0]),'/',str(last_stop[1])]) + ',')
            for task in tasks:
                if last_stop == task.location:
                    # append stop to csv (write in csv performing task task.name
                    csvfile.write('T,')

        csvfile.write('end')

def create_simulation_txt(best_plan, graph, tasks):
    import os

    # Define the path to the text file
    current_directory = os.path.dirname(__file__)
    current_directory = current_directory[:-3]
    txt_path = os.path.join(current_directory, 'LuaSimulator/simulator_data.txt')

    # Open the text file at a specific location
    with open(txt_path, 'w') as txtfile:
        # Append first element to txt (last stop)
        last_stop = best_plan.path[0]
        txtfile.write(''.join([str(last_stop[0]), '/', str(last_stop[1])]) + ',')
        for stop in best_plan.path[1:]:
            a, b = last_stop
            c, d = stop
            key = ((a, b), (c, d))
            path_tiles = graph[key][0]
            # For each tile in graph
            for tile in path_tiles[1:]:
                # Append tile to txt (last_stop)
                last_stop = tile
                txtfile.write(''.join([str(last_stop[0]), '/', str(last_stop[1])]) + ',')
            for task in tasks:
                if last_stop == task.location:
                    # Append stop to txt (write in txt performing task task.name)
                    txtfile.write('T,')

        txtfile.write('end')

    # close csv


