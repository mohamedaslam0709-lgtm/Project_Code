# ✈️ Indian Airlines Booking System

A console-based **Airline Ticket Booking System** built with **Python** and **MySQL**. This project simulates a real-world airline booking workflow, allowing passengers to sign up, book flights, and check status, while cashiers can manage and approve bookings.

It was built to demonstrate understanding of **Object-Oriented Programming (OOP)**, **Database Management**, **Password Security**, and **Input Validation**.

## 🚀 Key Features

### 👤 Passenger Module
- **Sign Up / Sign In:** Secure registration with password hashing (`bcrypt`).
- **Book Flights:** View available flights, select a flight, and book tickets.
- **Input Validation:** Prevents invalid inputs (e.g., non-numeric ages, weak passwords).
- **Booking Status:** View current booking status (Pending, Approved, etc.).
- **Cancel Tickets:** Ability to cancel booked flights.

### 💼 Cashier (Admin) Module
- **Secure Login:** Separate authentication for administrative staff.
- **View Bookings:** See a list of all passenger bookings in a formatted table.
- **Approve/Reject:** Manually approve pending bookings or mark them as not approved.

### 🛠️ Technical Highlights
- **Database:** Uses **MySQL** with **Connection Pooling** for efficient resource management.
- **Security:** Passwords are hashed using `bcrypt` before storing them in the database.
- **Data Display:** Uses the `tabulate` library to render pretty, grid-style tables in the terminal.
- **Environment Variables:** Sensitive credentials (DB passwords, etc.) are stored in a `.env` file for security.
- **Error Handling:** Includes `try-except` blocks to handle invalid inputs and database errors gracefully.

## 🛠️ Technologies Used

| Technology | Purpose |
| :--- | :--- |
| **Python 3** | Core logic and OOP structure |
| **MySQL** | Database storage for users and bookings |
| **mysql-connector-python** | Python library to connect to MySQL |
| **bcrypt** | Secure password hashing |
| **tabulate** | Formatting data into readable tables |
| **python-dotenv** | Managing environment variables |
| **Git/GitHub** | Version control |

## 📂 Project Structure

```text
airlines-booking-system/
│
├── .env                  # Store your DB credentials here (DO NOT COMMIT)
├── main.py               # The main application file (copy your code here)
├── README.md             # This file
└── requirements.txt      # List of required Python packages
```
## 📖 How It Works
 - **Initialization:** When the app starts, it creates the airlines_db database and necessary tables (bookings, Pid_tracker, Cashier_login) if they don't exist.
 - **Passenger Flow:** A user signs up -> gets a unique ID (e.g., AM1000) -> logs in -> books a flight -> status becomes "Pending".
 - **Cashier Flow:** A cashier logs in -> views all pending bookings -> approves a specific booking -> status updates to "Approved".
 - **Session Management:** The app tracks the current_user_session to keep users logged in until they choose to exit.

## 🎓 What I Learned
### Building this project helped me understand:

 - How to structure a large Python script using Classes and Static Methods.
 - The importance of Database Connection Pooling for performance.
 - How to securely store passwords using Hashing.
 - Handling User Input Validation to prevent crashes.
 - Managing Environment Variables to keep secrets safe.

## 🤝 Contributing

 - **This is a learning project. Feel free to fork it, suggest improvements, or use it as a reference for your own projects!**

## 📄 License
 - This project is **open-source** and available for educational purposes.
