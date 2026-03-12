class Car:
    def __init__(self, car_id):
        self.id = car_id
        self.pos = (0, 0)
        self.current_time = 0
        self.rides = []
    
    def update_pos(self,new_x,new_y):
        self.pos = (new_x, new_y)

    def get_current_pos(self):
        return (self.pos[0], self.pos[1])
    
    def distance_to (self, row , col):
        return abs (self.pos[0] - row) + abs(self.pos[1] - col)
    
    def time_available_at(self , ride):
        travel = self.distance_to(ride.startX, ride.startY)
        arrival = self.current_time + travel
        return max (arrival, ride.earliest_start)
    
    def assign_ride(self, ride):
        start_time = self.time_available_at(ride)
        travel_to_finish = abs(ride.startX - ride.endX) + abs(ride.startY - ride.endY)
        self.current_time = start_time + travel_to_finish
        self.position = (ride.endX, ride.endY)
        self.rides.append(ride.id)

class Ride:
    def __init__(self, ride_id, startX, startY, endX, endY, earliest_time, latest_time):
        self.id = ride_id
        self.startX = startX
        self.startY = startY
        self.endX = endX
        self.endY = endY
        self.earliest_time = earliest_time
        self.latest_time = latest_time
        self.distance = abs (endX - startX) + abs(endY - startY)

class Problem:
    def __init__(self, rows, cols, fleet_size, num_rides, bonus, time_steps):
        self.rows = rows
        self.cols = cols
        self.fleet_size = fleet_size
        self.num_rides = num_rides
        self.bonus = bonus
        self.time_steps = time_steps
        self.rides = []
