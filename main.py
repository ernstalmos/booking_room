import sys
from datetime import datetime
from database import get_connection, create_tables

ROOMS = [1, 2, 3, 4, 5]

def get_input(prompt):
    print(prompt, end=' ', flush=True)
    return sys.stdin.readline().strip()

def parse_datetime(dt_str):
    try:
        return datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
    except ValueError:
        return None

def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, email, phone FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(name, email, phone):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (name, email, phone) VALUES (?, ?, ?)', (name, email, phone))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id

def is_room_free(room_number, start_time, end_time):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT users.name, booking.end_time FROM booking
        JOIN users ON booking.user_id = users.id
        WHERE booking.room_number = ?
          AND (
            (booking.start_time <= ? AND booking.end_time > ?)
            OR
            (booking.start_time < ? AND booking.end_time >= ?)
            OR
            (booking.start_time >= ? AND booking.end_time <= ?)
          )
        LIMIT 1
    ''', (
        room_number,
        start_time, start_time,
        end_time, end_time,
        start_time, end_time,
    ))
    result = cursor.fetchone()
    conn.close()
    return result

def book_room():
    print('Available rooms:', ROOMS)
    try:
        room_number = int(get_input('Enter room number to book:'))
        if room_number not in ROOMS:
            print('Invalid room number.')
            return
    except ValueError:
        print('Invalid input.')
        return

    start_str = get_input('Enter start time (YYYY-MM-DD HH:MM):')
    end_str = get_input('Enter end time (YYYY-MM-DD HH:MM):')

    start_time = parse_datetime(start_str)
    end_time = parse_datetime(end_str)
    if not start_time or not end_time or end_time <= start_time:
        print('Invalid date format or end time is before start time.')
        return

    conflict = is_room_free(room_number, start_str, end_str)
    if conflict:
        occupant, busy_until = conflict
        print(f'Room is occupied by {occupant} until {busy_until}')
        return

    email = get_input('Enter your email:')
    user = get_user_by_email(email)

    if user:
        user_id, user_name, user_email, user_phone = user
        print(f'User found: {user_name}, Email: {user_email}, Phone: {user_phone}')
    else:
        print('User not found. Creating new user.')
        name = get_input('Enter your name:')
        phone = get_input('Enter your phone number:')
        user_id = create_user(name, email, phone)
        user_name = name
        user_email = email
        user_phone = phone

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO booking (room_number, start_time, end_time, user_id)
        VALUES (?, ?, ?, ?)
    ''', (room_number, start_str, end_str, user_id))
    conn.commit()
    conn.close()

    print('Booking successful!')
    print(f'\nNotification sent to {user_email} and {user_phone}')
    print(f'You booked Room #{room_number} from {start_str} to {end_str}.\n')

def check_room():
    print('Available rooms:', ROOMS)
    try:
        room_number = int(get_input('Enter room number to check:'))
        if room_number not in ROOMS:
            print('Invalid room number.')
            return
    except ValueError:
        print('Invalid input.')
        return

    check_time_str = get_input('Enter time to check (YYYY-MM-DD HH:MM):')
    check_time = parse_datetime(check_time_str)
    if not check_time:
        print('Invalid date format.')
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT users.name, booking.end_time FROM booking
        JOIN users ON booking.user_id = users.id
        WHERE booking.room_number = ?
          AND booking.start_time <= ? AND booking.end_time > ?
        LIMIT 1
    ''', (room_number, check_time_str, check_time_str))
    result = cursor.fetchone()
    conn.close()

    if result:
        occupant, busy_until = result
        print(f'Room is occupied by {occupant} until {busy_until}')
    else:
        print('Room is free at that time.')

def main():
    create_tables()
    while True:
        print('\nSelect action:')
        print('1 - Check room')
        print('2 - Book room')
        print('0 - Exit')
        choice = get_input('Enter choice:')
        if choice == '1':
            check_room()
        elif choice == '2':
            book_room()
        elif choice == '0':
            print('Goodbye.')
            break
        else:
            print('Invalid choice.')

if __name__ == '__main__':
    main()