from flask import Flask, render_template, request, redirect, url_for
import csv
import time
import os
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pickle
from selenium.common.exceptions import NoSuchElementException


# Define the login_and_save_session function
def login_and_save_session(username, password):
    """Login and save the session cookies to a file."""
    driver = initialize_driver()  # Use your existing driver setup
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(2)

    # Locate and fill the login form
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    
    time.sleep(60)  # Wait for the login process to complete
    
    # Save cookies to a session file
    cookies = driver.get_cookies()
    with open(SESSION_FILE, "wb") as file:
        pickle.dump(cookies, file)
    
    print("Session saved successfully!")
    driver.quit()


app = Flask(__name__)

SESSION_FILE = "session.pkl"

# Set Chrome options to run in headless mode
def get_chrome_path():
    """Check if Chrome path is set in the environment variable or use a default."""
    chrome_path = os.getenv("CHROME_PATH")
    
    if not chrome_path:
        # If CHROME_PATH is not set, try default locations
        if os.name == 'nt':  # Windows
            chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        elif os.name == 'posix':  # macOS/Linux
            chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        
        if not os.path.exists(chrome_path):
            raise Exception("Chrome executable not found. Please set the CHROME_PATH environment variable or provide the correct path.")
    
    return chrome_path

def initialize_driver():
    """Initialize the Chrome WebDriver in headless mode, with optional custom Chrome path."""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument("--headless")  # Ensure headless mode is enabled
    chrome_options.add_argument("--disable-gpu")  # Disable GPU acceleration
    chrome_options.add_argument("--window-size=1920x1080")  # Set window size (important for some websites)

    # Debugging: Confirm headless mode is set
    if "--headless" in chrome_options.arguments:
        print("Headless mode is enabled.")
    else:
        print("Headless mode is NOT enabled.")

    # Get the correct Chrome path from environment variable or default
    chrome_path = get_chrome_path()
    chrome_options.binary_location = chrome_path  # Set custom Chrome path

    # Use webdriver_manager to handle ChromeDriver installation
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver


def locate_element_with_fallback(driver, xpaths):
    """Locate an element by trying multiple fallback XPaths."""
    for xpath in xpaths:
        try:
            element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
            return element
        except NoSuchElementException:
            continue
    raise Exception("Element could not be located with any known XPaths.")

def fix_csv_delimiter(file_path):
    """Check and fix the delimiter in a CSV file."""
    with open(file_path, 'r', newline='', encoding='utf-8') as infile:
        first_line = infile.readline()

        # Check if the delimiter is a semicolon
        if ';' in first_line:
            print("Detected semicolon delimiter, fixing the file...")
            # Create a new file with commas as delimiters
            fixed_file_path = file_path.replace(".csv", "_fixed.csv")
            with open(fixed_file_path, 'w', newline='', encoding='utf-8') as outfile:
                # Replace all semicolons with commas
                for line in infile:
                    outfile.write(line.replace(';', ','))
            return fixed_file_path
        else:
            print("Delimiter is already correct (comma), no changes needed.")
            return file_path
        

# Updated code snippet to click on the correct user
def send_dm(target_username, message_text, name, follow_after=False):
    """Send a DM to the specified username and ensure correct user selection based on name."""
    print(f"Attempting to send DM to {name} ({target_username})...")

    driver = initialize_driver()  # Initialize in headless mode
    driver.get("https://www.instagram.com")
    time.sleep(2)

    # Load cookies to stay logged in
    try:
        with open(SESSION_FILE, "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)
        driver.refresh()
        time.sleep(2)
    except FileNotFoundError:
        print("No saved session found. Please log in first.")
        driver.quit()
        return "Session not found. Please log in first."

    try:
        driver.get("https://www.instagram.com/direct/new/")
        time.sleep(5)

        # Dismiss the "Turn on Notifications" popup if it appears
        try:
            not_now_button = locate_element_with_fallback(driver, [
                "//button[text()='Not Now']",
                "//button[contains(@class, 'HoLwm')]",
                "//button[text()='Not now']",
                "//button[contains(text(), 'Later')]"
            ])
            not_now_button.click()
            print("Notifications popup dismissed.")
            time.sleep(2)
        except Exception:
            print("No 'Turn on Notifications' popup appeared or could not be clicked.")

        # Click the "Send message" button
        send_message_button = locate_element_with_fallback(driver, [
            "//div[@role='button' and text()='Send message']",
            "//button[contains(text(), 'Send message')]",
            "//div[contains(@class, 'x1ey2m1c') and contains(@role, 'button')]"
        ])
        send_message_button.click()
        print("Clicked 'Send message' button.")
        time.sleep(2)

        # Search for user and select the first result
        recipient_input = locate_element_with_fallback(driver, [
            "//input[@name='queryBox']", "//input[@placeholder='Search...']"
        ])
        print(f"Entering username: {target_username}")
        recipient_input.send_keys(target_username)
        time.sleep(3)

        # Get the names of the accounts in the search results
        search_results = driver.find_elements(By.XPATH, "//span[contains(text(), '')]")
        print(f"Found {len(search_results)} search results.")

        # Loop through search results to match the name (substring match)
        found = False
        for result in search_results:
            user_name = result.text.strip()
            print(f"Checking account: '{user_name}'")

            if user_name and name.strip().lower() in user_name.lower():
                print(f"Found the correct user: {user_name}")
                driver.execute_script("arguments[0].scrollIntoView(true);", result)
                time.sleep(1)

                driver.execute_script("arguments[0].click();", result)  # Click on the result directly
                time.sleep(2)
                found = True
                break

        if not found:
            print(f"Couldn't find {name} in search results. Skipping.")
            driver.quit()
            return f"Error: Could not find {name} in search results."

        # Click "Message" button to open chat window
        print("Clicking the 'Message' button.")
        message_button = locate_element_with_fallback(driver, [
            "//div[text()='Message' or text()='Chat']",
            "//button[contains(@class, 'sqdOP')]"
        ])
        message_button.click()
        time.sleep(5)

        # Locate the message box and send the message
        try:
            print("Locating message box to send the message.")
            message_box = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//p[contains(@class, 'xat24cr') and contains(@class, 'xdj266')]"))
            )
            message_box.click()
            message_box.send_keys(message_text)
            message_box.send_keys(Keys.RETURN)

            print("Message sent, waiting for 10 seconds before proceeding...")
            time.sleep(10)

        except Exception as e:
            print(f"Error sending message: {e}")
            driver.quit()
            return f"Error sending message: {e}"

        # Follow the user if specified
        if follow_after:
            print("Following the user...")
            follow_button = locate_element_with_fallback(driver, [
                "//button[text()='Follow']",
                "//button[contains(@class, 'sqdOP')]"
            ])
            follow_button.click()
            time.sleep(2)
            print("User followed successfully.")

        return "Message sent successfully."

    except Exception as e:
        print(f"Error sending message: {e}")
        driver.quit()
        return f"Error sending message: {e}"
    finally:
        driver.quit()





@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    login_and_save_session(username, password)
    return redirect(url_for("home"))

import csv
import os

def fix_csv_delimiter(file_path):
    """Check and fix the delimiter in a CSV file, preserving the header."""
    with open(file_path, 'r', newline='', encoding='utf-8') as infile:
        content = infile.readlines()

        if ';' in content[0]:  # Check if semicolon is used in the header
            print("Detected semicolon delimiter, fixing the file...")
            fixed_file_path = file_path.replace(".csv", "_fixed.csv")
            with open(fixed_file_path, 'w', newline='', encoding='utf-8') as outfile:
                header = content[0].replace(";", ",")
                outfile.write(header)

                for line in content[1:]:
                    outfile.write(line.replace(";", ","))
            return fixed_file_path
        else:
            print("Delimiter is already correct (comma), no changes needed.")
            return file_path


import csv
import os
LOG_FILE = "dm_log.csv"  # Define the log file name


@app.route("/send_bulk_dms", methods=["POST"])
def send_bulk_dms():
    # Get the uploaded CSV file
    csv_file = request.files["csv_file"]
    message_delay = int(request.form["message_delay"])
    num_dms = int(request.form["num_dms"])
    follow_after = "follow_after" in request.form

    # Ensure the 'uploads' directory exists
    upload_folder = 'uploads'
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # Save the CSV file temporarily in the 'uploads' directory
    csv_file_path = os.path.join(upload_folder, csv_file.filename)
    csv_file.save(csv_file_path)

    # Fix delimiter if needed
    fixed_csv_path = fix_csv_delimiter(csv_file_path)

    # Initialize log to store message results
    log = []

    # Read the CSV file and send DMs
    progress_index = read_progress()  # Read progress from the file

    with open(fixed_csv_path, "r", newline='', encoding='utf-8') as file:
        csv_reader = csv.reader(file, delimiter=",")  # Ensure comma delimiter
        header = next(csv_reader)  # Read and store the header (skip it manually)

        print(f"Header: {header}")  # Debugging: print the header

        if header != ['name', 'username', 'message']:
            print("Warning: The header doesn't match the expected format!")
            return "Error: Invalid CSV header."

        count = 0
        # Skip rows up to the progress index
        for _ in range(progress_index):
            next(csv_reader)  # Skip the rows before the progress point

        for row in csv_reader:
            # Skip empty rows or rows with insufficient data
            if len(row) < 3 or not any(row):  # Check for empty or invalid rows
                print(f"Skipping invalid row: {row}")
                continue

            # Unpack the row into name, username, and message
            name, username, message = row
            print(f"Sending DM to {name} ({username})...")

            # Send the DM and capture the result
            result = send_dm(username, message, name, follow_after)  # Pass the 'name' field
            
            # Log the result: "Sent" if successful, or error message if failed
            log.append([name, username, message, "Sent" if "successfully" in result else f"Failed: {result}"])
            
            count += 1
            time.sleep(message_delay)

            # Update progress after each message sent
            update_progress(count)  # Update the progress file

    # Write the log to CSV after processing all messages
    with open(LOG_FILE, "w", newline='', encoding='utf-8') as log_file:
        log_writer = csv.writer(log_file)
        log_writer.writerow(["Name", "Username", "Message", "Status"])  # Header for the log file
        log_writer.writerows(log)

    os.remove(csv_file_path)  # Clean up the uploaded file

    return render_template("index.html", result=f"{count} DMs sent. Log saved as {LOG_FILE}.")


PROGRESS_FILE = "progress.txt"  # Define the progress file

def read_progress():
    """Read the progress from the file, if it exists. Returns the index to start from."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as file:
            progress = file.read()
            if progress.isdigit():
                return int(progress)
    return 0  # If no progress file or empty, start from the beginning


def update_progress(index):
    """Update the progress in the progress file."""
    with open(PROGRESS_FILE, 'w') as file:
        file.write(str(index))


if __name__ == "__main__":
    app.run(debug=True)
