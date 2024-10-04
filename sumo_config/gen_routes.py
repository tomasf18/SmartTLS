import sys
from sumo_utils import generate_route_file

if __name__ == "__main__":
    simulation_path = sys.argv[1]
    generate_route_file("sumo_config/" + simulation_path + ".rou.xml")
    