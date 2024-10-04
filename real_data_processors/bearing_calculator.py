from math import radians, degrees, atan2, cos, sin

class BearingCalculator:
    def __init__(self, obj_lat, obj_lon, tl_lat=40.632503243454174, tl_lon=-8.648470238587695):
        self.tl_lat = tl_lat
        self.tl_lon = tl_lon
        self.obj_lat = obj_lat
        self.obj_lon = obj_lon

    @property
    def bearing(self):
        d_lon = radians(self.tl_lon - self.obj_lon)
        lat1 = radians(self.obj_lat)
        lat2 = radians(self.tl_lat)

        y = sin(d_lon) * cos(lat2)
        x = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(d_lon)

        bearing = atan2(y, x)
        bearing = degrees(bearing)
        bearing = (bearing + 360) % 360  # Normalize to 0-360 degrees

        return bearing if bearing < 180 else bearing - 360

# Coordinates provided by the user
bc = BearingCalculator(40.632307323041516, -8.64844006373914)

print(bc.bearing)
