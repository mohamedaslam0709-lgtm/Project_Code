## 1. Prerequisites
 - Python 3.8 or higher
 - MySQL Server (running locally or remote)
 - Git
## 2. Clone the Repository
 - In your CMD or Command Prompt, type or paste the following lines:
```text
git clone https://github.com/mohamedaslam0709-lgtm/Flight_Database.git
cd Flight_Database
```
 - This installs the folder in your default directory.
 - If you want it elsewhere, you can simply point the file to your destination by:
```text
cd <your_path>
<your_drive_letter>
```
 - If your preferred path is in another partition like Local drive D, then type ```d:``` instead of ```<your_drive_letter>```.
 - For example, ```cd d:/my_github/my_folder``` then followed by ```d:```.
 - Now, you can see the CMD line start from ```d:\my_github\my_folder>```.
 - Then proceed with 'Step 2', which will copy the entire folder in the selected end path.
## 3. Install Dependencies
```text
pip install -r requirements.txt
```
## 4. Configure Environment Variables
 - Open a file named ```.env``` in the cloned directory. Copy and paste the below lines into the file and edit your Database details:
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
 - You can run this code in your own IDE or through CMD with the following command:
 - Make sure your CMD path is the same as the cloned folder path by referring to 'Step 2'.
 - Type ```python main.py```. This initializes the ```main.py``` file
 - Make sure that ```MySQL80``` service is running in 'Services' or ```mysqld``` in your 'Task Manager', else it will throw an ```ERROR```.
