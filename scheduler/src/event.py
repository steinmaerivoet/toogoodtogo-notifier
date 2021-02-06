class Event:

    def __init__(self, creation_date, store, items_available, pickup_start_time, pickup_end_time):
        self.creation_date = creation_date
        self.store = store
        self.items_available = items_available
        self.pickup_start_time = pickup_start_time
        self.pickup_end_time = pickup_end_time
