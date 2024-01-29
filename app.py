from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__, template_folder='template')

bus_numbers = ['SM1', 'SM2', 'SM3', 'SM4', 'SM5', 'SM6', 'SM7', 'SM8', 'SM9', 'SM10']
available_seats = [f'seat{i}' for i in range(1, 33)]

seat_status = {seat: {'status': 'Available', 'name': None, 'bus_number': None,
                      'pickup_location': None, 'pickup_time': None,
                      'return_pickup_location': None, 'reservation_time': None} for seat in available_seats}

reserved_pickup_locations = {}
reserved_return_pickup_locations = {}
reserved_buses = {}

@app.route('/')
def home():
    return render_template('index.html', bus_numbers=bus_numbers)

# Updated driver_dashboard function
@app.route('/driver_dashboard')
def driver_dashboard():
    reserved_seats = [seat for seat, status_info in seat_status.items() if status_info['status'] == 'Reserved']

    # Count of reserved and available seats for each bus
    reserved_seats_count = {bus_number: sum(1 for status_info in seat_status.values() if
                                           status_info['status'] == 'Reserved' and status_info['bus_number'] == bus_number)
                            for bus_number in bus_numbers}

    available_seats_count = {bus_number: len(available_seats) - reserved_seats_count[bus_number]
                             for bus_number in bus_numbers}

    pickup_details = {
        'pickup_location_count': count_reserved_locations('pickup_location'),
        'return_pickup_location_count': count_reserved_locations('return_pickup_location'),
        'bus_count': count_reserved_buses(),
        'pickup_time_count': count_pickup_times(),
        'seat_availability': get_seat_availability(),
        'reserved_seats_count': reserved_seats_count,
        'available_seats_count': available_seats_count  # Add this line for available seats count
    }

    return render_template('driver_dashboard.html', reserved_seats=reserved_seats, pickup_details=pickup_details,
                           seat_status=seat_status)

def count_reserved_locations(location_type):
    locations_count = {}
    for seat, status_info in seat_status.items():
        if status_info['status'] == 'Reserved':
            location = status_info[location_type]
            if location:
                locations_count[location] = locations_count.get(location, 0) + 1
    return locations_count

def count_reserved_buses():
    buses_count = {}
    for seat, status_info in seat_status.items():
        if status_info['status'] == 'Reserved':
            bus_number = status_info['bus_number']
            buses_count[bus_number] = buses_count.get(bus_number, 0) + 1
    return buses_count

def count_pickup_times():
    pickup_times_count = {}
    for seat, status_info in seat_status.items():
        if status_info['status'] == 'Reserved':
            pickup_time = status_info['pickup_time']
            pickup_location = status_info['pickup_location']
            if pickup_time:
                if pickup_time not in pickup_times_count:
                    pickup_times_count[pickup_time] = {'count': 0, 'locations': []}
                pickup_times_count[pickup_time]['count'] += 1
                if pickup_location:
                    pickup_times_count[pickup_time]['locations'].append(pickup_location)
    return pickup_times_count

def get_seat_availability():
    seat_availability = {}
    for bus_number in bus_numbers:
        reserved_seats_count = sum(1 for status_info in seat_status.values() if
                                   status_info['status'] == 'Reserved' and status_info['bus_number'] == bus_number)
        available_seats_count = len(available_seats) - reserved_seats_count
        seat_availability[bus_number] = {'reserved': reserved_seats_count, 'available': available_seats_count}
    return seat_availability

@app.route('/book', methods=['POST'])
def book():
    if request.method == 'POST':
        name = request.form['name']
        pickup_location = request.form['pickup_location']
        pickup_time = request.form['pickup_time']
        seat_number = request.form['seat_number']
        bus_number = request.form['bus_number']
        return_pickup_location = request.form['return_pickup_location']

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if seat_status[seat_number]['status'] == 'Available':
            seat_status[seat_number] = {'status': 'Reserved', 'name': name, 'bus_number': bus_number,
                                         'pickup_location': pickup_location, 'pickup_time': pickup_time,
                                         'return_pickup_location': return_pickup_location,
                                         'reservation_time': current_time}

            update_reserved_locations_count('pickup_location', pickup_location)
            update_reserved_locations_count('return_pickup_location', return_pickup_location)
            update_reserved_buses_count(bus_number)

            # Check if the bus is fully booked
            if reserved_buses[bus_number] >= len(available_seats):
                mark_fully_booked(bus_number)

            return render_template('booking_success.html', name=name, bus_number=bus_number, seat_number=seat_number,
                                   pickup_location=pickup_location, pickup_time=pickup_time,
                                   return_pickup_location=return_pickup_location, reservation_time=current_time)
        else:
            return render_template('booking_failed.html', name=name)

def update_reserved_locations_count(location_type, location):
    reserved_locations_count = reserved_pickup_locations if location_type == 'pickup_location' else reserved_return_pickup_locations
    if location:
        reserved_locations_count[location] = reserved_locations_count.get(location, 0) + 1

def update_reserved_buses_count(bus_number, increment=True):
    if increment:
        reserved_buses[bus_number] = reserved_buses.get(bus_number, 0) + 1
    else:
        if bus_number in reserved_buses and reserved_buses[bus_number] > 0:
            reserved_buses[bus_number] -= 1

def mark_fully_booked(bus_number):
    # Additional logic to mark the bus as fully booked
    # You can set a flag or update a status in your data structure
    # For example: reserved_buses[bus_number] = 'Fully Booked'
    pass

@app.route('/cancel', methods=['POST'])
def cancel():
    if request.method == 'POST':
        cancel_name = request.form['cancel_name']

        for seat, status_info in seat_status.items():
            if status_info['status'] == 'Reserved' and status_info['name'] == cancel_name:
                pickup_location = status_info['pickup_location']
                return_pickup_location = status_info['return_pickup_location']
                bus_number = status_info['bus_number']

                seat_status[seat] = {'status': 'Available', 'name': None, 'bus_number': None,
                                     'pickup_location': None, 'pickup_time': None,
                                     'return_pickup_location': None, 'reservation_time': None}

                update_reserved_locations_count('pickup_location', pickup_location)
                update_reserved_locations_count('return_pickup_location', return_pickup_location)
                update_reserved_buses_count(bus_number, increment=False)

                return f"Cancellation successful for {cancel_name}. Seat {seat} is now available."

        return f"No reservation found for {cancel_name}"

@app.route('/get_available_seats', methods=['POST'])
def get_available_seats():
    reserved_seats = [seat for seat, status_info in seat_status.items() if status_info['status'] == 'Reserved']
    available_seats_list = [seat for seat in available_seats if seat not in reserved_seats]
    return jsonify(available_seats=available_seats_list)

if __name__ == '__main__':
    app.run(debug=True)
