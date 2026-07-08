import mysql.connector
from mysql.connector import pooling, Error
import bcrypt
from tabulate import tabulate
import re
import os
from dotenv import load_dotenv

# =============================================================================
# GLOBAL SESSION MANAGEMENT
# =============================================================================

current_user_session = None 

# =============================================================================
# DATABASE INITIALIZATION & POOLING
# =============================================================================

def init_db():
    """
    Initializes the MySQL database, creates tables if they don't exist,
    and sets up a connection pool for efficient database access.
    """
    global db_pool
    try:  
        load_dotenv()
        pool_siz = int(os.getenv("POOL_SIZE", 5))

        # Step 1: Temporary connection to create the database if it doesn't exist
        temp_cn = mysql.connector.connect(
            user = os.getenv("USER_NAME"),
            password = os.getenv("PASSWORD"),
            host = os.getenv("HOST"),
            auth_plugin = 'mysql_native_password' 
        )
        temp_cursor = temp_cn.cursor()
        temp_cursor.execute('''CREATE DATABASE IF NOT EXISTS airlines_db''')
        temp_cursor.close()
        temp_cn.close()

        # Step 2: Create a connection pool for the main application
        db_pool = pooling.MySQLConnectionPool(
            pool_name = os.getenv("POOL_NAME", "localpool"),
            pool_size = pool_siz,
            user = os.getenv("USER_NAME"),
            password = os.getenv("PASSWORD"),
            host = os.getenv("HOST"),
            database = os.getenv("DATABASE", "airlines_db"),
            auth_plugin = 'mysql_native_password'
        )
    except Error as e:
        print(f"Failed to initialize database or pool: {e}")
        db_pool = None
        return

    db = Database()

    # Verify database creation
    result = db.execute_query("""SHOW DATABASES LIKE 'airlines_db'""")
    if not result:
        db.execute_query('''CREATE DATABASE IF NOT EXISTS airlines_db''')

    # =====================================================================
    # CREATE BOOKINGS TABLE IF NOT EXISTS
    # =====================================================================

    result = db.execute_query("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'airlines_db' AND table_name = 'bookings'"""
    )

    if not result[0][0]:
        db.execute_query('''
            CREATE TABLE IF NOT EXISTS bookings (
                Pid VARCHAR(20) PRIMARY KEY,
                Create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                Modified_time DATETIME ON UPDATE CURRENT_TIMESTAMP,
                Name VARCHAR(50),
                Gender VARCHAR(10),
                Age INT,
                Flight_ID INT,
                Airline VARCHAR(50),
                Tickets INT,
                Total INT,
                Departure VARCHAR(50),
                Destination VARCHAR(50),
                Status VARCHAR(20),
                Password_Hash VARCHAR(255)
            )'''
        )
        db.execute_query('''CREATE INDEX idx_pid ON bookings (Pid)''')

    # =====================================================================
    # CREATE PID TRACKER TABLE (For generating unique Passenger IDs)
    # =====================================================================

    result = db.execute_query("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'airlines_db' AND table_name = 'Pid_tracker'
    """)

    if not result[0][0]:
        db.execute_query('''
            CREATE TABLE Pid_tracker (Current_value INT AUTO_INCREMENT PRIMARY KEY)'''
        )
        db.update_query("""
            INSERT IGNORE INTO Pid_tracker (Current_value)
            VALUES (1000)"""
        )

    # =====================================================================
    # CREATE CASHIER LOGIN TABLE
    # =====================================================================

    result = db.execute_query("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'airlines_db' AND table_name = 'Cashier_login'
    """)

    if not result[0][0]:
        db.execute_query('''
            CREATE TABLE Cashier_login (
            Cashier_name VARCHAR(10) PRIMARY KEY,
            Cashier_pwd VARCHAR(90))'''
        )
        cashier_pwd = os.getenv("CASHIER_PASS")
        hashed_pwd = bcrypt.hashpw(cashier_pwd.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        db.update_query("""
            INSERT IGNORE INTO Cashier_login (Cashier_name, Cashier_pwd) 
            VALUES (%s, %s)""",
            (os.getenv("CASHIER_NAME"), hashed_pwd)
        )


# =============================================================================
# DATABASE HELPER CLASS
# =============================================================================

class Database():
    """
    Wrapper class for database operations using connection pooling.
    Handles query execution, committing, and error handling.
    """
    def __init__(self):
        global db_pool
        # Check if db_pool was successfully created
        if 'db_pool' not in globals() or db_pool is None:
            raise RuntimeError("Database pool not initialized. Check init_db() errors.")
        self.db_pool = db_pool 

    def execute_query(self, query, params = None, commit = False, dictionary = False):
        """
        Executes a SQL query:
        :param--query: SQL query string
        :param--params: Parameters for the query (optional)
        :param--commit: If True, commits the transaction
        :param--dictionary: If True, returns results as dictionaries
        :return: Fetched rows or None
        """
        connect = self.db_pool.get_connection()
        try:
            cursor = connect.cursor(dictionary = dictionary)
            cursor.execute(query, params or ())
            
            if commit:
                connect.commit()
                return None
            
            if cursor.description:
                return cursor.fetchall()
            else:
                connect.commit()
                return None
                
        except Error as e:
            print(f"Database error: {e}")
            connect.rollback()
            raise
        finally:
            connect.close()

    def update_query(self, query, params = None):
        """
        Helper method to execute an UPDATE/INSERT/DELETE query with auto-commit.
        """
        self.execute_query(query, params, commit = True)


# Initialize the database and tables on module load
init_db()

# =============================================================================
# PASSENGER & FLIGHT DATA MANAGEMENT
# =============================================================================

class Details:  
    """
    Static utility class for managing passenger data and flight details.
    Uses a class-level dictionary to cache passenger data in memory.
    """
    Passengers = {}
    
    @staticmethod
    def create_passenger_ID(Name, Gender):
        """
        Generates a unique Passenger ID based on Name, Gender, and a sequential number.
        Format: FirstLetter(Name) + FirstLetter(Gender) + Counter (e.g., AM1000)
        """
        db = Database()
        result = db.execute_query("""SELECT Current_value from Pid_tracker""")
        
        if not result:
            raise ValueError("Pid_tracker table is empty!")
            
        Pid_num = result[0][0]
        Pid = Name[0].upper() + Gender[0].upper() + str(Pid_num)
        return Pid, Pid_num
    
    @staticmethod
    def load_passengers():
        """
        Loads all passenger records from the database into the in-memory Passengers dictionary.
        """
        db = Database()
        rows = db.execute_query("""SELECT * FROM bookings""", dictionary = True)
        Details.Passengers.clear()
        for row in rows:
            Details.Passengers[row["Pid"]] = [
                row["Pid"],
                row["Name"],
                row["Gender"],
                row["Age"],
                row["Password_Hash"], 
                row["Flight_ID"],
                row["Airline"],
                row["Tickets"],
                row["Total"],
                row["Departure"],
                row["Destination"],
                row["Status"],
                row["Create_time"],
                row["Modified_time"]
            ]

    @staticmethod
    def store_passenger_data(Pid):
        """
        Inserts a new passenger record into the bookings table with initial status.
        """
        db = Database()
        pas = Details.Passengers.get(Pid)
        if not pas:
            return

        db.update_query("""
            INSERT IGNORE INTO bookings (Pid, Name, Gender, Age, Password_Hash, Status)
            VALUES (%s, %s, %s, %s, %s, %s)""",
            (pas[0], pas[1], pas[2], int(pas[3]), pas[4], pas[5])
        )

    def store_flight_data(self, Pid, Plane_ID, Ticket_count, Ticket_total):
        """
        Updates an existing passenger record with flight details and sets status to 'Pending'.
        """
        db = Database()
        fd = flight_details()

        if Plane_ID not in fd:
            print("Invalid Flight ID!")
            return
        
        flight = fd[Plane_ID]
        db.update_query("""
            UPDATE bookings SET 
                Flight_ID = %s, 
                Airline = %s, 
                Tickets = %s, 
                Total = %s, 
                Departure = %s, 
                Destination = %s, 
                Status = %s 
            WHERE Pid = %s""",
            (Plane_ID, flight[0], Ticket_count, Ticket_total, flight[2], flight[3], "Pending", Pid)
        )

# Load existing passengers into memory at startup
# Only load passengers if the database pool exists

if 'db_pool' in globals() and db_pool is not None:
    Details.load_passengers()
else:
    print("Skipping passenger load: Database not initialized.")

# =============================================================================
# PASSENGER USER INTERFACE
# =============================================================================

class Passenger:
    """
    Handles passenger authentication (Sign Up/Sign In) and menu navigation.
    """
    def signup(self):
        """
        Handles new passenger registration with input validation and password security.
        """
        try:
            # Name Validation
            while True:
                Name = input("Enter your Name: ").upper()
                if len(Name) > 3 and Name.isalpha():
                    print(f"Your name: {Name}\n")
                    break
                else:
                    print("\nName should not contain numbers or special characters.\nIt should be 3 or more letters.")
                    continue

            # Gender Validation
            while True:
                Gender = input("Enter your gender (Male/Female): ").strip().upper()    
                if Gender in ["MALE", "FEMALE"]:
                    print(f"Your gender: {Gender}\n")
                    break
                else:
                    print("Please type either 'Male' or 'Female'")
                    continue

            # Age Validation
            while True:
                try:
                    Age = int(input("Enter your age: ").strip())
                    if str(Age).isdigit() and Age > 17:
                        print(f"Your age: {Age}\n")
                        break
                    else:
                        print("\nYou must be 18 or older to proceed!")
                        continue
                except ValueError:
                    print("\nInvalid age format! Please enter a number.")
    
            # Password Validation
            while True:
                Password = input(
                    "Create a password\n"
                    "Enter: "
                ).strip()

                has_len = len(Password) >= 6
                has_num = re.search('[0-9]', Password) is not None
                has_upper = re.search('[A-Z]', Password) is not None
                has_special = re.search('[^a-zA-Z0-9]', Password) is not None

                if has_len and has_num and has_upper and has_special:
                    print("Your password seems fine.\n")
                    break  # Exits Password loop, proceeds to SignUp
                else:
                    if not has_len:
                        print("Password must be at least 6 characters long.")
                    if not has_num:
                        print("Password must contain at least one number.")
                    if not has_upper:
                        print("Password must contain at least one uppercase letter.")
                    if not has_special:
                        print("Password must contain at least one special character.")

        except ValueError:
            print("\nInvalid input! Try Again!")
            return

        # Hash password and create ID
        hashed_pwd = bcrypt.hashpw(Password.encode(), bcrypt.gensalt())
        Pid, Pid_num = Details.create_passenger_ID(Name, Gender)

        db = Database()
        Details.Passengers[Pid] = [
            Pid, Name, Gender, Age, hashed_pwd.decode(), "Yet to book"
        ]
        Details.store_passenger_data(Pid)

        # Increment the counter for next ID
        db.update_query("""UPDATE Pid_tracker SET Current_value = %s""", (Pid_num + 1,))
        print(f"Signup successful!\nYour ID is: {Pid}.\nYou can now sign into your ID.")

    def signin(self):
        """
        Authenticates a user with their Passenger ID and password.
        """
        try:
            Pid = input("Enter your Passenger_ID: ").strip().upper()
            if Pid not in Details.Passengers:
                print("Invalid Passenger_ID")
                return 

            stored_hashed_pwd = Details.Passengers[Pid][4]
            Password = input("Enter your password: \n").strip()

            if not bcrypt.checkpw(Password.encode(), stored_hashed_pwd.encode()):
                print("Incorrect Password")
                return
            
        # Set session and display menu
            global current_user_session
            current_user_session = self
            self.session_ID = Pid
            print(f"\nWelcome {Details.Passengers[Pid][1]}!")
            self.passenger_menu()
            
        except Exception as e:
            print(f"Enter valid credentials! {e}")

    def passenger_menu(self):
        """
        Main loop for passenger options.
        """
        while True:
            print("\n1. View Flights & Book ticket")
            print("2. Cancel booked ticket")
            print("3. View booking status")
            print("4. Exit\n")
            try:
                choice = int(input("Enter your choice: ").strip())
                if choice == 4:
                    print("Signing out...")
                    global current_user_session
                    current_user_session = None
                    break 
                flight_book.view_book(choice, self.session_ID)

            except ValueError:
                print("Invalid choice. Enter a number.")


# =============================================================================
# FLIGHT DATA & BOOKING LOGIC
# =============================================================================

def flight_details():
    """
    Returns a dictionary of available flights.
    Key: Flight ID, Value: [Airline, Fare, Departure, Destination]
    """
    flight = {
        101: ["Kingfisher", 1500, "Trichy", "Chennai"],
        102: ["Indigo", 2000, "Trichy", "Bangalore"],
        103: ["Vistara", 2500, "Trichy", "Hyderabad"],
        104: ["Emirates", 3500, "Chennai", "Kochi"]
    }
    return flight


class flight_book:
    """
    Handles flight viewing, booking, cancellation, and status checking.
    """
    @staticmethod
    def view_book(ch, Pid):
        dt = Details()
        db = Database()
        fd = flight_details()

        if ch == 1:
            # Displays available flights
            table = [
                [fid, flight[0], flight[1], flight[2], flight[3]]
                for fid, flight in fd.items()
            ]
            headers = ["FlightID", "Airlines", "Fare", "From", "To"]
            if input("\nPress Enter to book tickets: ").strip() == "":
                # Checks if user already has a pending booking
                check = db.execute_query('''SELECT Status FROM bookings WHERE Pid=%s''', (Pid,))
                if check and check[0][0] in ["Pending", "Not Approved"]:
                    print("\nYou have a booked ticket.\nCancel it to book again!")
                    return
                    
                print(tabulate(table, headers, colalign=('left',), tablefmt="fancy_grid"))

                max_tries = 3
                attempts = 0
                while attempts < max_tries:
                    try:
                        Plane_ID = int(input("\nEnter Flight ID: "))
                        
                        if Plane_ID not in fd:
                            print("\nInvalid Flight ID!")
                            attempts += 1
                            if attempts >= max_tries:
                                print("Maximum attempts reached. Returning to menu.")
                                return
                            continue
                        
                        Ticket_count = int(input("Enter number of tickets: "))
                        if Ticket_count < 1 or Ticket_count > 50:
                            print(f"\nInvalid number of tickets. Must be between 1 and 50.")
                            attempts += 1
                            if attempts >= max_tries:
                                print("Maximum attempts reached. Returning to menu.")
                                return
                            continue

                        Fare = fd[Plane_ID][1]
                        Ticket_total = Fare * Ticket_count
                        print(f"Total Price: {Ticket_total}")

                        if input("Confirm booking? (Yes/No): ").lower().strip() == 'yes':
                            dt.store_flight_data(Pid, Plane_ID, Ticket_count, Ticket_total)
                            print(f"\nSuccess! Booked {Ticket_count} tickets for Flight ID {Plane_ID}.")
                            Details.load_passengers()
                            return
                        else:
                            print("\nBooking Cancelled!")
                            return
                        
                    except ValueError:
                        print("\nInvalid input!\nOnly numbers allowed. Try again!")
                        attempts += 1
                        if attempts >= max_tries:
                            print("\nMaximum attempts reached.\nReturning to menu.")
                            return                     
            
        elif ch == 2:
            # Cancel booking
            rows = db.execute_query('''
                SELECT Pid, Name, Gender, Age, Flight_ID, Airline, Tickets, Total, Status, 
                COALESCE(DATE_FORMAT(Modified_time, '%r\n%W'), 'None') as BookedTime,
                COALESCE(DATE_FORMAT(Modified_time, '%d-%m-%Y'), 'None') as BookedDate
                FROM bookings WHERE Pid = %s''', (Pid,), dictionary = True)
 
            for row in rows:
                check_cancel = row['Status']

                if check_cancel == 'Yet to book':
                    print("\nNo booked ticket found. Book a ticket to cancel!")
                    return
                
                print("\n")
                print(tabulate(rows, headers = "keys", tablefmt = 'fancy_grid', stralign = "center"))

                id = row['Flight_ID']
                confirm = input("\n\nDo you confirm cancelling the ticket? (yes/no) : ").strip().lower()
                if confirm != 'yes':
                    print("\nAction terminated!")
                    return
                 
                cancel = int(input("\nEnter the Flight_ID to cancel: "))
                if cancel != id:
                    print("\nInvalid Flight_ID. Enter a valid ID!")
                    return

            # Resets booking fields
            db.update_query("""
            UPDATE bookings SET 
                Flight_ID = %s, 
                Airline = %s, 
                Tickets = %s, 
                Total = %s, 
                Departure = %s, 
                Destination = %s, 
                Status = %s 
            WHERE Pid = %s""",
            ("0", "-", "0", "0", "-", "-", "Yet to book", Pid))

            Details.load_passengers()
            print("\nCancelled successfully!\n")

        elif ch == 3:
            # View Status
            rows = db.execute_query('''
                SELECT Pid, Name, Gender, Age, Flight_ID, Airline, Tickets, Total, Status, 
                COALESCE(DATE_FORMAT(Modified_time, '%r\n%W'), 'None') as BookedTime,
                COALESCE(DATE_FORMAT(Modified_time, '%d-%m-%Y'), 'None') as BookedDate
                FROM bookings WHERE Pid = %s''', (Pid,), dictionary = True)
            
            print("\n")
            print(tabulate(rows, headers = "keys", tablefmt = 'fancy_grid', stralign = "center"))

        else:
            print("Invalid choice or input. Try again!")
            return
        
# =============================================================================
# CASHIER MODULE: ADMIN INTERFACE FOR BOOKING MANAGEMENT
# =============================================================================

class Cashier:
    """
    Handles cashier administrative tasks such as
    viewing, approving, and canceling passenger bookings.
    """

    def login(self):
        """
        Authenticates the cashier against the stored credentials in the database.
        """
        db = Database()
        # Fetches the cashier record from the database:
        try:  
            # Prompt user input
            name = input("Enter cashier name: ").strip().upper()
            pwd = input("Enter password: ").strip()

            # Fetch the stored hash for the user
            result = db.execute_query(
                "SELECT Cashier_pwd FROM Cashier_login WHERE Cashier_name = %s",
                (name,)
            )
            # Validate credentials
            if not result:
                print("Invalid Cashier Name.")
                return
            
            stored_hash = result[0][0]
            
            # Verifies password against the hash
            if bcrypt.checkpw(pwd.encode('utf-8'), stored_hash.encode('utf-8')):
                print(f"\n Welcome {name}!")
                self.menu()
            else:
                print("❌ Incorrect Password.")

        except Exception as e:
            print(f"An error occurred: {e}")

    def menu(self):
        """
        Main loop for cashier operations: View, Approve, Cancel, Exit.
        """
        db = Database()

        while True:
            print("\n1. View all Bookings")
            print("2. Approve by ID")
            print("3. Cancel by ID")
            print("4. Exit")
            try:
                ch = int(input("Enter your choice: ").strip())

                # -------------------------------------------------------------
                # OPTION 1: VIEW ALL BOOKINGS
                # -------------------------------------------------------------

                rows = db.execute_query('''
                        SELECT Pid, Name, Gender, Age, Flight_ID, Airline, Tickets, Total, Status, 
                        COALESCE(DATE_FORMAT(Modified_time, '%r|%W'), 'None') as BookedTime,
                        COALESCE(DATE_FORMAT(Modified_time, '%d-%m-%Y'), 'None') as BookedDate
                        FROM bookings''', 
                        dictionary = True
                    )
                if ch == 1:
                    if not rows:
                        print("\nNo bookings found.")
                    else:
                        # Checks and clears NULL date/time values for display
                        for row in rows:
                            if row['BookedTime'] == 'None':
                                row['BookedTime'] = "-"
                            if row['BookedDate'] == 'None':
                                row['BookedDate'] = "-"
                        
                        print("\n")
                        print(tabulate(rows, headers="keys", tablefmt='fancy_grid', stralign="center"))

                # -------------------------------------------------------------
                # OPTION 2: APPROVE BOOKING BY ID
                # -------------------------------------------------------------

                elif ch == 2:
                    if not rows:
                        print("\nNo bookings found.")
                        continue
                    pid = input("Enter the PID to approve: ").strip()
                    rows = db.execute_query('''SELECT Pid, Flight_ID FROM bookings WHERE Pid = %s''', (pid,), dictionary = True)

                    found = False
                    for row in rows:
                        if not row['Pid']:
                            print("Invalid ID! Booking not found.")
                            continue
                        elif not row['Flight_ID']:
                            print('No booked tickets found. Cannot approve empty field!')
                        else:
                            # Update status to 'Approved'
                            db.update_query('''UPDATE bookings SET Status = %s WHERE Pid = %s''', ('Approved', pid))
                            Details.load_passengers()
                            print("Action successful!")
                            found = True
                    
                    if not found:
                        print("No valid booking found for this PID.")
                
                # -------------------------------------------------------------
                # OPTION 3: CANCEL BOOKING BY ID
                # -------------------------------------------------------------

                elif ch == 3:
                    if not rows:
                        print("\nNo bookings found.")
                        continue
            
                    pid = input("Enter the ID to cancel: ").strip()
                    row = db.execute_query('''SELECT Pid FROM bookings WHERE Pid = %s''', (pid,))
                    
                    if not row:
                        print("Invalid ID! Booking not found.")
                        continue
                    
                    # Updates status to 'Not Approved'
                    db.update_query('''UPDATE bookings SET Status = %s WHERE Pid = %s''', ('Not Approved', pid))
                    Details.load_passengers()
                    print("Action successful!")
                
                # -------------------------------------------------------------
                # OPTION 4: EXIT
                # -------------------------------------------------------------

                elif ch == 4:
                    print("Logging out!...")
                    break

                else:
                    print("Invalid choice! Try again.")
                    continue
            except Exception as e:
                print(f"An error occurred: {e}")


# =============================================================================
# MAIN EXECUTION LOOP
# =============================================================================

if __name__ == "__main__":
    """
    Entry point of the application. Handles the main menu for Passenger, Cashier, or Exit.
    """
    while True:
        try:
            print("\n", "*" * 24, "Welcome to Indian Airbus", "*" * 24)
            
            if current_user_session:
                print(f"Logged in as: {current_user_session.session_ID}")
                print("1. Go to Menu\n2. Sign Out")
                choice = input("Enter choice: ").strip()
                if choice == '2':
                    current_user_session = None
                    continue
                elif choice == '1':
                    current_user_session.passenger_menu()
                    continue
                else:
                    continue
            
            # If not logged in, shows main menu
            print("1. Passenger")
            print("2. Cashier")
            print("3. Exit")
            
            choice = int(input("Enter your choice: "))

            if choice == 1:
                p = Passenger()
                opt = int(input("1. Sign Up\n2. Sign In\nEnter: "))
                if opt == 1:
                    p.signup()
                else:
                    p.signin()

            elif choice == 2:
                c = Cashier()
                c.login()
                
            elif choice == 3:
                print("\nThank you for visiting!\n")
                break
                
        except ValueError:
            print("Incorrect selection! Try Again!")
            continue
