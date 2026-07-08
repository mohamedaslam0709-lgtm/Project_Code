## 1. Prerequisites
 - Python 3.8 or higher
 - MySQL Server (running locally or remote)

## 2. Clone the Repository
```text
git clone https://github.com/mohamedaslam0709-lgtm/Flight_Database.git
cd Flight_Database
```
## 3. Install Dependencies
```text
pip install -r requirements.txt
```
## 4. Configure Environment Variables
 - Create a file named ```.env``` in the root directory and add your MySQL details:
```text
USER_NAME=root
PASSWORD=your_mysql_password
HOST=localhost
DATABASE=airlines_db
POOL_SIZE=5
CASHIER_NAME=admin
CASHIER_PASS=your_secure_admin_password
```
**⚠️ Security Note: Never commit your .env file to GitHub. It is already listed in .gitignore.**
## 5. Run the Application
 - You can run this code in your own IDE.
 - Make sure that ```MySQL80``` service is running in 'Services' or ```mysqld``` in your 'Task Manager'.
 - Consult 'README.md' or official docs in case of any error.
