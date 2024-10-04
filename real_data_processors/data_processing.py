import json
from math import radians, cos, sin, asin, sqrt
from datetime import datetime
import threading
import time
import argparse  # Para processar argumentos de linha de comando
import sys

SENSOR_DISTANCE = 60
MINIMUM_SPEED = 1.1
CACHE_TIMEOUT = 60
OLD_DATA_TIMEOUT = 1
TL_INFO_FILE_PATH = "tl_info.json"

# P33 location: 40.63245, -8.64859
class DataProcessor:
    def __init__(self, traffic_light_lat=40.63245, traffic_light_lon=-8.64859, json_file_path="test1.json"):
        self.traffic_light_lat = traffic_light_lat
        self.traffic_light_lon = traffic_light_lon

        # ---
        self.current_time = None
        self.total_counter = 0
        self.cars_list = {}
        self.type_value = {
            "Bus": 5,
            "Car": 1
        }
        
        # --- 
        # Accumulated waiting times
        self.vehicles_stop_timestamp = {}
        self.vehicles_last_timestamp = {}
        self.accumulated_waiting_times = {}
        self.accumulated_waiting_times_cache = {}
        self.accumulated_waiting_times_cache["cached_data_time_control"] = datetime.now()
        self.currently_waiting = {}

        print(f"Starting data processing for file: {json_file_path}")
        processing_thread = threading.Thread(target=self.read_and_process_data, args=(json_file_path,))
        processing_thread.start()


    # Function to calculate distance between two coordinates using the Haversine formula
    def haversine(self, lon1, lat1, lon2, lat2):
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        r = 6371000  # Earth radius in meters
        distance = c * r
        return distance


    def read_and_process_data(self, file_path):
        print(f"Reading data from file: {file_path}")
        with open(file_path, "r") as file:
            for line in file:
                time.sleep(0.03)  # Simulating data processing delay
                data = json.loads(line)
                self.process_data(data)
        print("Data processing completed!")
    
    def get_tl_heading_range(self):
        with open(TL_INFO_FILE_PATH, "r") as file:
            for line in file:
                tl_info = json.loads(line)
                if tl_info["coordinates"] == [self.traffic_light_lat, self.traffic_light_lon]:
                    return tl_info["heading_range"][0], tl_info["heading_range"][1]    


    def process_data(self, object):

        event_timestamp_str = object["eventTimestamp"]["$date"]
        event_timestamp = datetime.fromisoformat(event_timestamp_str.replace("Z", "+00:00"))
        
        self._clean_up_cache()
        self._clean_up_old_data(event_timestamp)
        self._check_timestamp(event_timestamp)

        # -- Process new data --
        vehicle_id = object["entityId"]
        vehicle_type = object["entityType"]
        coordinates = object["location"]["coordinates"]
        speed = object["speed"]
        heading = object["heading"]
        
        distance = self.haversine(coordinates[0], coordinates[1], self.traffic_light_lon, self.traffic_light_lat)

        print(f"\n\nProcessing vehicle {vehicle_id} with speed {speed:.2f} m/s at time {event_timestamp_str}.")

        if self.is_vehicle_valid_to_process(distance, heading):
            self._handle_waiting_time(vehicle_id, speed, event_timestamp)
            self._handle_total_counter(vehicle_type, vehicle_id)
    
    
    def _clean_up_cache(self):
        if (datetime.now() - self.accumulated_waiting_times_cache["cached_data_time_control"]).total_seconds() > CACHE_TIMEOUT:
            # print("\nCache has expired. Clearing the cache.")
            self.accumulated_waiting_times_cache = {}
            self.accumulated_waiting_times_cache["cached_data_time_control"] = datetime.now()
    
    
    def _clean_up_old_data(self, event_timestamp):
        vehicles_old_data = []

        for vehicle in self.vehicles_last_timestamp:
            if (event_timestamp - self.vehicles_last_timestamp[vehicle]).total_seconds() > OLD_DATA_TIMEOUT:
                vehicles_old_data.append(vehicle)

        for vehicle in vehicles_old_data:
            # print(f"\nRemoving vehicle {vehicle} because stopped receiving data of it.")
            del self.vehicles_last_timestamp[vehicle]
            if vehicle in self.vehicles_stop_timestamp:
                del self.vehicles_stop_timestamp[vehicle]
            if vehicle in self.accumulated_waiting_times:
                del self.accumulated_waiting_times[vehicle]
            if vehicle in self.currently_waiting:
                del self.currently_waiting[vehicle]
                
    
    def _handle_vehicle_accelerating(self, vehicle_id):
        if vehicle_id in self.currently_waiting:
            # print(f"Vehicle {vehicle_id} is no longer waiting. Removing from the waiting list.")
            del self.vehicles_stop_timestamp[vehicle_id]
        # Store the value in the cache for eventual future reuse
        self.accumulated_waiting_times_cache[vehicle_id] = self.accumulated_waiting_times[vehicle_id]
        
    
    def _handle_vehicle_remaining_stopped(self, vehicle_id, event_timestamp):
        delta_t = (event_timestamp - self.vehicles_stop_timestamp[vehicle_id]).total_seconds()
        if vehicle_id in self.accumulated_waiting_times_cache:
            self.accumulated_waiting_times[vehicle_id] = self.accumulated_waiting_times_cache[vehicle_id] + delta_t
        else:
            self.accumulated_waiting_times[vehicle_id] = delta_t
        print(f"Vehicle {vehicle_id} has been stopped for {self.accumulated_waiting_times[vehicle_id]:.2f} seconds.")
        self.currently_waiting[vehicle_id] = event_timestamp
        
    
    def _handle_vehicle_stopping(self, vehicle_id, event_timestamp):
        # print(f"Vehicle {vehicle_id} has just stopped.")
        self.vehicles_stop_timestamp[vehicle_id] = event_timestamp
        self.accumulated_waiting_times[vehicle_id] = 0
    
    
    def _handle_waiting_time(self, vehicle_id, speed, event_timestamp):
        if vehicle_id in self.vehicles_stop_timestamp:
            if speed >= MINIMUM_SPEED:
                print(f"Vehicle {vehicle_id} is accelerating.")
                self._handle_vehicle_accelerating(vehicle_id)
            else:
                print(f"Vehicle {vehicle_id} is still stopped.")
                self._handle_vehicle_remaining_stopped(vehicle_id, event_timestamp)
        else:
            if speed < MINIMUM_SPEED:
                print(f"Vehicle {vehicle_id} has stopped.")
                self._handle_vehicle_stopping(vehicle_id, event_timestamp)

        self.vehicles_last_timestamp[vehicle_id] = event_timestamp
    
    
    def _handle_total_counter(self, vehicle_type, vehicle_id):
        if vehicle_id not in self.cars_list:
            value = self.type_value.get(vehicle_type, 1)
            self.total_counter += value
            self.cars_list[vehicle_id] = vehicle_type
    
    
    def _check_timestamp(self, event_timestamp):
        """
        Check if the timestamp of the current data is different from the current time.
        If it is, reset the counter and the list of cars to guarantee that the counting of the vehicles is done in the same instant.
        """
        if self.current_time is None:
            self.current_time = event_timestamp
        
        if event_timestamp > self.current_time:
            self.current_time = event_timestamp
            self.total_counter = 0
            self.cars_list = {}
            
    def is_vehicle_valid_to_process(self, distance, heading):
        min_degree, max_degree = self.get_tl_heading_range()
        return distance <= SENSOR_DISTANCE and min_degree <= heading <= max_degree
    
    def get_total_waiting_time(self):
        total_time = sum(self.accumulated_waiting_times.values())
        print(f"\n** Total accumulated waiting time: {total_time:.2f} seconds")
        return total_time
    
    
    def get_total_counter(self):
        print(f"** Total vehicles: {self.total_counter}")
        return self.total_counter


if __name__ == "__main__":
    # Argument parsing
    parser = argparse.ArgumentParser(description="Process traffic data from a JSON file.")
    parser.add_argument("json_file", help="Path to the JSON file with traffic data.")
    args = parser.parse_args()

    processor = DataProcessor(json_file_path=args.json_file)

    for i in range(1000000):
        time.sleep(0.03) # Simulating data processing delay
        processor.get_total_waiting_time()
        processor.get_total_counter()
