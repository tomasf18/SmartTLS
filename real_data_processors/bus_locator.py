import json
from datetime import datetime
import threading
import time
import argparse  # Para processar argumentos de linha de comando


DATA_TIMEOUT = 5

class BusLocator:
    def __init__(self, json_file_path="test.json"):
        
        self.bus_location = {} # bus_id: ([lat, lon], timestamp)

        print(f"Starting data processing for file: {json_file_path}")
        processing_thread = threading.Thread(target=self.read_and_process_data, args=(json_file_path,))
        processing_thread.start()


    def read_and_process_data(self, file_path):
        print(f"Reading data from file: {file_path}\n")
        with open(file_path, "r") as file:
            for line in file:
                time.sleep(1)  # Simulating data processing delay
                data = json.loads(line)
                self.process_data(data)
        print("Data processing completed!")


    def process_data(self, object):
        
        entity_type = object["entityType"]
        
        if entity_type != "Bus":
            return

        event_timestamp_str = object["eventTimestamp"]["$date"]
        event_timestamp = datetime.fromisoformat(event_timestamp_str.replace("Z", "+00:00"))

        self._clean_up_old_data(event_timestamp)
        
        # -- Process new data --
        bus_id = object["entityId"]
        coordinates = object["location"]["coordinates"]

        # print(f"\n\nProcessing bus {bus_id} with coordinates {coordinates}")
        
        self.bus_location[bus_id] = (coordinates, event_timestamp)
   
    
    def _clean_up_old_data(self, event_timestamp):
        bus_old_data = []

        for bus in self.bus_location:
            if (event_timestamp - self.bus_location[bus][1]).total_seconds() > DATA_TIMEOUT:
                bus_old_data.append(bus)
                
        for bus in bus_old_data:
            # print(f"Removing old data for bus {bus} because stopped receiving updates of it.")
            del self.bus_location[bus]

 
    def get_bus_locations(self):
        data = list(self.bus_location.values())
        coordinates = [x[0] for x in data]
        print(f"** Bus locations: {coordinates}")


if __name__ == "__main__":
    # Argument parsing
    parser = argparse.ArgumentParser(description="Process bus data from a JSON file.")
    parser.add_argument("json_file", help="Path to the JSON file with bus data.")
    args = parser.parse_args()

    bus_locator = BusLocator(json_file_path=args.json_file)

    for i in range(1000000):
        time.sleep(1)
        bus_locator.get_bus_locations()
