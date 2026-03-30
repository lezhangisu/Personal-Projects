"""
Piazza Participation Grader with Tkinter UI

This module extracts student participation data from Piazza and updates Canvas grade CSV files.
It handles authentication with Piazza API, retrieves student participation data, and updates
the corresponding Canvas gradebook CSV with participation scores.

Beta 2.0 update:
    Add timestamp mode to filter out students who made posts outside the lecture time frame.

Author: Le Zhang
Version: 2.1 (with Tkinter UI and custom input directory)
Date: 2026-02-12
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
import os
import pandas as pd
import csv
from datetime import datetime, timedelta
import pytz
import threading
import json


class PiazzaGraderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Piazza Participation Grader")
        self.root.geometry("600x720")
        self.root.resizable(False, False)

        # Piazza section ID mapping
        self.PIAZZA_SECTION_IDS = {
            1: 'mkl3084fyrt3sf',
            2: 'mkl2w6rlkr44aj'
        }

        # Section default time mapping
        self.SECTION_DEFAULT_TIMES = {
            1: {"start": "08:20", "end": "10:10"},
            2: {"start": "15:55", "end": "17:45"}
        }

        # Variables to store input values
        self.section_number = tk.IntVar(value=1)
        self.lecture_number = tk.IntVar(value=1)
        self.start_post_id = tk.IntVar(value=1)
        self.end_post_id = tk.IntVar(value=1)
        self.lecture_date = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))

        # Initialize time variables with section 1 defaults
        self.lecture_start_time = tk.StringVar(value=self.SECTION_DEFAULT_TIMES[1]["start"])
        self.lecture_end_time = tk.StringVar(value=self.SECTION_DEFAULT_TIMES[1]["end"])

        # File/directory path variables
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.input_dir = tk.StringVar(value=script_dir)  # Directory containing base CSV files
        self.cookie_path = tk.StringVar(value=os.path.join(script_dir, "cookies.txt"))
        self.output_dir = tk.StringVar(value=os.path.join(script_dir, "output_timed"))

        # Create UI
        self.create_widgets()

        # Bind section number change event
        self.section_number.trace_add('write', self.on_section_change)

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title and author in the same row
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, sticky=tk.EW, pady=(0, 20))

        # Title (left side)
        title_label = ttk.Label(title_frame, text="Piazza Participation Grader",
                                font=('Arial', 16, 'bold'))
        title_label.pack(side=tk.LEFT)

        # Author information (right side)
        author_label = ttk.Label(title_frame, text="by Le Zhang",
                                font=('Arial', 10, 'italic'),
                                foreground='#666666')
        author_label.pack(side=tk.RIGHT)

        # Configure title_frame to expand and push items to edges
        title_frame.columnconfigure(0, weight=1)

        # Input fields
        row = 1

        # Section Number
        section_frame = ttk.Frame(main_frame)
        section_frame.grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=5)

        ttk.Label(section_frame, text="Section Number (1-2):", font=('Arial', 10)).pack(side=tk.LEFT)
        section_spinbox = ttk.Spinbox(section_frame, from_=1, to=2, textvariable=self.section_number,
                                     width=5, font=('Arial', 10))
        section_spinbox.pack(side=tk.LEFT, padx=(10, 0))

        # Add hint label for section times
        self.section_hint_label = ttk.Label(section_frame,
                                           text="(Section 1: 08:20-10:10 | Section 2: 15:55-17:45)",
                                           font=('Arial', 9, 'italic'),
                                           foreground='gray')
        self.section_hint_label.pack(side=tk.LEFT, padx=(10, 0))
        row += 1

        # Lecture Number
        ttk.Label(main_frame, text="Lecture Number (1-39):", font=('Arial', 10)).grid(
            row=row, column=0, sticky=tk.W, pady=5)
        lecture_spinbox = ttk.Spinbox(main_frame, from_=1, to=39, textvariable=self.lecture_number,
                                     width=10, font=('Arial', 10))
        lecture_spinbox.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        row += 1

        # Starting Post Number
        ttk.Label(main_frame, text="Starting Post Number:", font=('Arial', 10)).grid(
            row=row, column=0, sticky=tk.W, pady=5)
        start_spinbox = ttk.Spinbox(main_frame, from_=1, to=200, textvariable=self.start_post_id,
                                   width=10, font=('Arial', 10))
        start_spinbox.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        row += 1

        # Ending Post Number
        ttk.Label(main_frame, text="Ending Post Number:", font=('Arial', 10)).grid(
            row=row, column=0, sticky=tk.W, pady=5)
        end_spinbox = ttk.Spinbox(main_frame, from_=1, to=200, textvariable=self.end_post_id,
                                 width=10, font=('Arial', 10))
        end_spinbox.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        row += 1

        # Lecture Date
        ttk.Label(main_frame, text="Lecture Date (YYYY-MM-DD):", font=('Arial', 10)).grid(
            row=row, column=0, sticky=tk.W, pady=5)
        date_entry = ttk.Entry(main_frame, textvariable=self.lecture_date, width=15, font=('Arial', 10))
        date_entry.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        row += 1

        # Lecture Time Frame
        time_frame = ttk.LabelFrame(main_frame, text="Lecture Time Frame (Chicago Time)", padding="10")
        time_frame.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=10)

        # Start Time
        ttk.Label(time_frame, text="Start Time (HH:MM):", font=('Arial', 10)).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.start_time_entry = ttk.Entry(time_frame, textvariable=self.lecture_start_time,
                                          width=10, font=('Arial', 10))
        self.start_time_entry.grid(row=0, column=1, sticky=tk.W)

        # End Time
        ttk.Label(time_frame, text="End Time (HH:MM):", font=('Arial', 10)).grid(
            row=0, column=2, sticky=tk.W, padx=(20, 10))
        self.end_time_entry = ttk.Entry(time_frame, textvariable=self.lecture_end_time,
                                        width=10, font=('Arial', 10))
        self.end_time_entry.grid(row=0, column=3, sticky=tk.W)

        # Add note about auto-set times
        time_note = ttk.Label(time_frame,
                              text="Note: Times auto-set based on section, but you can modify them",
                              font=('Arial', 8, 'italic'),
                              foreground='gray')
        time_note.grid(row=1, column=0, columnspan=4, pady=(5, 0))

        row += 1

        # Input directory selection (containing base CSV files)
        input_dir_frame = ttk.LabelFrame(main_frame, text="Input Directory (with base CSV files)", padding="10")
        input_dir_frame.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=10)

        input_dir_entry = ttk.Entry(input_dir_frame, textvariable=self.input_dir,
                                    width=50, font=('Arial', 9))
        input_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        browse_input_btn = tk.Button(input_dir_frame, text="Browse",
                                     command=self.browse_input_dir,
                                     fg="black", bg="#f0f0f0", font=('Arial', 9))
        browse_input_btn.pack(side=tk.RIGHT)

        # Show the expected filename format
        filename_label = ttk.Label(input_dir_frame,
                                  text="Format: S2026-CPRE-2810-01-base.csv",
                                  font=('Arial', 8, 'italic'),
                                  foreground='gray')
        filename_label.pack(anchor=tk.W, pady=(5, 0))

        row += 1

        # Cookie file selection
        cookie_frame = ttk.LabelFrame(main_frame, text="Cookie File", padding="10")
        cookie_frame.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=10)

        cookie_entry = ttk.Entry(cookie_frame, textvariable=self.cookie_path,
                                 width=50, font=('Arial', 9))
        cookie_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        browse_cookie_btn = tk.Button(cookie_frame, text="Browse",
                                      command=self.browse_cookie_file,
                                      fg="black", bg="#f0f0f0", font=('Arial', 9))
        browse_cookie_btn.pack(side=tk.RIGHT)

        row += 1

        # Output directory selection
        output_frame = ttk.LabelFrame(main_frame, text="Output Directory", padding="10")
        output_frame.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=10)

        output_entry = ttk.Entry(output_frame, textvariable=self.output_dir,
                                 width=50, font=('Arial', 9))
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        browse_output_btn = tk.Button(output_frame, text="Browse",
                                      command=self.browse_output_dir,
                                      fg="black", bg="#f0f0f0", font=('Arial', 9))
        browse_output_btn.pack(side=tk.RIGHT)

        row += 1

        # Progress bar and status - with extra padding
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.grid(row=row, column=0, columnspan=3, sticky=tk.EW, pady=(20, 15))

        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 8))

        self.status_label = ttk.Label(self.progress_frame, text="Ready", font=('Arial', 9))
        self.status_label.pack()

        row += 1

        # Execute button - with plenty of space above and below
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=3, pady=(20, 30))

        self.execute_btn = tk.Button(button_frame, text="Get Grades", command=self.execute_grader,
                                     fg="black",
                                     bg="#4CAF50",
                                     font=('Arial', 11, 'bold'),
                                     width=15,
                                     height=1,
                                     relief=tk.RAISED,
                                     bd=2,
                                     activebackground="#45a049",
                                     activeforeground="white",
                                     cursor="hand2")
        self.execute_btn.pack()

        row += 1

        # Log area - with extra top padding
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.grid(row=row, column=0, columnspan=3, sticky=tk.NSEW, pady=(15, 10))

        # Create text widget with scrollbar
        self.log_text = tk.Text(log_frame, height=8, width=70, font=('Courier', 9))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(row, weight=1)

    def browse_input_dir(self):
        """Browse for input directory containing base CSV files"""
        directory = filedialog.askdirectory(title="Select Directory with Base CSV Files")
        if directory:
            self.input_dir.set(directory)

    def browse_cookie_file(self):
        filename = filedialog.askopenfilename(
            title="Select Cookie File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.cookie_path.set(filename)

    def browse_output_dir(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir.set(directory)

    def log_message(self, message):
        """Add message to log area"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def execute_grader(self):
        """Execute the grading process in a separate thread"""
        # Validate inputs
        if not self.validate_inputs():
            return

        # Disable execute button
        self.execute_btn.config(state=tk.DISABLED)
        self.progress_bar.start(10)
        self.status_label.config(text="Processing...")
        self.log_text.delete(1.0, tk.END)

        # Run in separate thread to keep UI responsive
        thread = threading.Thread(target=self.run_grader)
        thread.daemon = True
        thread.start()

    def on_section_change(self, *args):
        """Handle section number change - auto-set default times"""
        try:
            section = self.section_number.get()
            if section in self.SECTION_DEFAULT_TIMES:
                # Get current time values
                current_start = self.lecture_start_time.get()
                current_end = self.lecture_end_time.get()
                default_start = self.SECTION_DEFAULT_TIMES[section]["start"]
                default_end = self.SECTION_DEFAULT_TIMES[section]["end"]

                # Only auto-set if current times are empty or match the other section's defaults
                # This prevents overriding user modifications
                if (current_start == "" or current_start == self.SECTION_DEFAULT_TIMES[1]["start"] or
                    current_start == self.SECTION_DEFAULT_TIMES[2]["start"]):
                    self.lecture_start_time.set(default_start)

                if (current_end == "" or current_end == self.SECTION_DEFAULT_TIMES[1]["end"] or
                    current_end == self.SECTION_DEFAULT_TIMES[2]["end"]):
                    self.lecture_end_time.set(default_end)

                # Update hint label color to indicate active section
                if section == 1:
                    self.section_hint_label.config(foreground='#4CAF50')  # Green for section 1
                else:
                    self.section_hint_label.config(foreground='#2196F3')  # Blue for section 2

        except tk.TclError:
            pass  # Ignore errors when section number is being edited

    def validate_inputs(self):
        """Validate user inputs"""
        try:
            # Validate section number
            section = self.section_number.get()
            if section not in [1, 2]:
                messagebox.showerror("Error", "Section number must be 1 or 2")
                return False

            # Validate lecture number
            lecture = self.lecture_number.get()
            if lecture < 1 or lecture > 39:
                messagebox.showerror("Error", "Lecture number must be between 1 and 39")
                return False

            # Validate post numbers
            start = self.start_post_id.get()
            end = self.end_post_id.get()
            if start < 1 or start > 200 or end < 1 or end > 200:
                messagebox.showerror("Error", "Post numbers must be between 1 and 200")
                return False
            if start > end:
                messagebox.showerror("Error", "Starting post number must be ≤ ending post number")
                return False

            # Validate date format
            try:
                datetime.strptime(self.lecture_date.get(), '%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Use YYYY-MM-DD")
                return False

            # Validate time format
            try:
                start_time = self.lecture_start_time.get().strip()
                end_time = self.lecture_end_time.get().strip()

                # Check if times are empty
                if not start_time or not end_time:
                    messagebox.showerror("Error", "Start time and end time cannot be empty")
                    return False

                # Validate time format
                datetime.strptime(start_time, '%H:%M')
                datetime.strptime(end_time, '%H:%M')

            except ValueError:
                messagebox.showerror("Error", "Invalid time format. Use HH:MM (24-hour format)")
                return False

            # Check input directory exists
            if not os.path.exists(self.input_dir.get()):
                messagebox.showerror("Error", f"Input directory not found:\n{self.input_dir.get()}")
                return False

            # Check cookie file
            if not os.path.exists(self.cookie_path.get()):
                messagebox.showerror("Error", f"Cookie file not found:\n{self.cookie_path.get()}")
                return False

            return True

        except tk.TclError:
            messagebox.showerror("Error", "Invalid input values")
            return False

    def run_grader(self):
        """Main grading process"""
        try:
            # Get input values
            section_number = self.section_number.get()
            lecture_number = self.lecture_number.get()
            start_post_id = self.start_post_id.get()
            end_post_id = self.end_post_id.get()
            lecture_date = self.lecture_date.get()
            start_time = self.lecture_start_time.get()
            end_time = self.lecture_end_time.get()
            input_directory = self.input_dir.get()

            # Construct input CSV file path based on section number
            input_csv_file = os.path.join(
                input_directory,
                f"S2026-CPRE-2810-0{section_number}-base.csv"
            )

            self.log_message("=" * 50)
            self.log_message("Starting Piazza Participation Grader")
            self.log_message("=" * 50)
            self.log_message(f"Section: {section_number}")
            self.log_message(f"Lecture: {lecture_number}")
            self.log_message(f"Post Range: {start_post_id} - {end_post_id}")
            self.log_message(f"Date: {lecture_date}")
            self.log_message(f"Time Frame: {start_time} - {end_time} (Central Time)")
            self.log_message(f"Input Directory: {input_directory}")
            self.log_message(f"Input CSV File: {os.path.basename(input_csv_file)}")

            # Check if input CSV file exists
            if not os.path.exists(input_csv_file):
                error_msg = f"ERROR: Input CSV file not found:\n{input_csv_file}\n\nPlease ensure the file follows the format: S2026-CPRE-2810-0{section_number}-base.csv"
                self.log_message(error_msg)
                self.show_error_dialog("File Not Found", error_msg)
                return

            # Get lecture time in UTC
            lecture_time_utc = self.get_lecture_time_utc(
                section_number, lecture_date, start_time, end_time
            )

            if not lecture_time_utc[0] or not lecture_time_utc[1]:
                error_msg = "ERROR: Failed to calculate lecture time"
                self.log_message(error_msg)
                self.show_error_dialog("Time Calculation Error", error_msg)
                return

            self.log_message(f"UTC Time: {lecture_time_utc[0]} - {lecture_time_utc[1]}")

            # Extract cookies
            self.log_message("\n[AUTHENTICATION]")
            piazza_session, session_id = self.extract_cookies_from_file(self.cookie_path.get())

            if not piazza_session or not session_id:
                error_msg = "ERROR: Failed to extract required cookies.\nPlease check your cookies.txt file."
                self.log_message(error_msg)
                self.show_error_dialog("Authentication Error", error_msg)
                return

            # Prepare authentication
            cookies = {
                'session_id': session_id,
                'piazza_session': piazza_session
            }
            csrf_token = session_id

            # Get class ID first
            class_id = self.PIAZZA_SECTION_IDS[section_number]

            # Test authentication with a simple request
            self.log_message("\n[TESTING AUTHENTICATION]")
            if not self.test_authentication(class_id, csrf_token, cookies):
                error_msg = "ERROR: Authentication failed.\nYour cookies may be expired or invalid."
                self.log_message(error_msg)
                self.show_error_dialog("Authentication Failed", error_msg)
                return

            # Retrieve student data
            self.log_message("\n[DATA RETRIEVAL]")
            self.log_message(f"Retrieving student participation for posts {start_post_id}-{end_post_id}...")

            participating_students = self.get_students_by_lecture(
                start_post_id, end_post_id, class_id, csrf_token, cookies, lecture_time_utc
            )

            if participating_students is None:
                error_msg = "ERROR: Failed to retrieve student data from Piazza.\nPlease check your network connection and try again."
                self.log_message(error_msg)
                self.show_error_dialog("Data Retrieval Error", error_msg)
                return

            if not participating_students:
                error_msg = "WARNING: No participating students found for the specified post range."
                self.log_message(error_msg)
                # Show warning but continue (might be empty class)
                if not messagebox.askyesno("No Students Found",
                                          "No participating students were found.\nDo you want to continue?"):
                    return

            self.log_message(f"✓ Found {len(participating_students)} valid participating students")

            # Process and save data
            self.log_message("\n[DATA PROCESSING]")

            # Set output file path
            output_csv_file = os.path.join(
                self.output_dir.get(),
                f"section0{section_number}-L{lecture_number}.csv"
            )

            # Process participation
            try:
                unmatched = self.process_student_participation(
                    input_csv_file, participating_students, lecture_number, output_csv_file
                )
            except Exception as e:
                error_msg = f"ERROR: Failed to process CSV data: {str(e)}"
                self.log_message(error_msg)
                self.show_error_dialog("CSV Processing Error", error_msg)
                return

            if unmatched is not None:
                self.log_message("\n[PROCESS COMPLETE]")
                if unmatched:
                    self.log_message(f"Note: {len(unmatched)} students could not be matched")
                    self.log_message("\nUnmatched students:")
                    for student in unmatched[:10]:  # Show first 10
                        self.log_message(f"  • {student[0]} ({student[1]})")
                    if len(unmatched) > 10:
                        self.log_message(f"  ... and {len(unmatched)-10} more")
                else:
                    self.log_message("All operations completed successfully")

                self.log_message(f"\nOutput saved to: {output_csv_file}")
                self.status_label.config(text="Completed successfully!")

                # Show success message
                self.root.after(0, lambda: messagebox.showinfo(
                    "Success",
                    f"Grading completed successfully!\n\n"
                    f"Found: {len(participating_students)} participating students\n"
                    f"Unmatched Students: {len(unmatched) if unmatched else 0}\n"
                    f"Output saved to:\n{output_csv_file}"
                ))
            else:
                self.status_label.config(text="Process interrupted")

        except requests.exceptions.RequestException as e:
            error_msg = f"Network Error: Failed to connect to Piazza.\n{str(e)}"
            self.log_message(f"\nERROR: {error_msg}")
            self.show_error_dialog("Network Error", error_msg)

        except json.JSONDecodeError as e:
            error_msg = f"Data Error: Invalid response from Piazza.\n{str(e)}"
            self.log_message(f"\nERROR: {error_msg}")
            self.show_error_dialog("Data Error", error_msg)

        except KeyError as e:
            error_msg = f"Data Structure Error: Unexpected response format from Piazza.\nMissing key: {str(e)}"
            self.log_message(f"\nERROR: {error_msg}")
            self.show_error_dialog("Data Format Error", error_msg)

        except Exception as e:
            error_msg = f"Unexpected Error: {str(e)}"
            self.log_message(f"\nERROR: {error_msg}")
            self.show_error_dialog("Unexpected Error", error_msg)

        finally:
            # Re-enable execute button
            self.root.after(0, self.reset_ui)

    def show_error_dialog(self, title, message):
        """Show error dialog in the main thread"""
        self.root.after(0, lambda: messagebox.showerror(title, message))

    def reset_ui(self):
        """Reset UI after processing"""
        self.progress_bar.stop()
        self.execute_btn.config(state=tk.NORMAL)

    def test_authentication(self, class_id, csrf_token, cookies):
        """Test if authentication is working"""
        try:
            test_data = {
                "method": "network.get_feeds",
                "params": {
                    "nid": class_id
                }
            }
            response = self.make_piazza_request(csrf_token, cookies, test_data)
            if response and 'result' in response:
                self.log_message("✓ Authentication successful")
                return True
            else:
                self.log_message("✗ Authentication failed")
                return False
        except Exception as e:
            self.log_message(f"✗ Authentication test failed: {str(e)}")
            return False

    # Original functions from the script, modified to use log_message and error handling
    def extract_cookies_from_file(self, file_path):
        """Extract Piazza session cookies from a text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                cookie_string = file.read().strip()

            cookies = {}
            for cookie in cookie_string.split('; '):
                if '=' in cookie:
                    key, value = cookie.split('=', 1)
                    cookies[key.strip()] = value.strip()

            piazza_session = cookies.get('piazza_session')
            session_id = cookies.get('session_id')

            if piazza_session:
                self.log_message("Successfully extracted: piazza_session")
            else:
                self.log_message("WARNING: piazza_session NOT FOUND")

            if session_id:
                self.log_message("Successfully extracted: session_id")
            else:
                self.log_message("WARNING: session_id NOT FOUND")

            return piazza_session, session_id

        except FileNotFoundError:
            self.log_message(f"ERROR: File '{file_path}' does not exist.")
            return None, None
        except Exception as e:
            self.log_message(f"ERROR: Failed to extract cookies - {e}")
            return None, None

    def make_piazza_request(self, csrf_token, cookies, data):
        """Make authenticated POST request to Piazza API"""
        session = requests.Session()
        session.headers.update({
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json',
            'csrf-token': csrf_token,
            'origin': 'https://piazza.com',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        session.cookies.update(cookies)
        response = session.post('https://piazza.com/logic/api', json=data)
        response.raise_for_status()  # Raise exception for bad status codes
        return response.json()

    def get_user_ids_from_post(self, class_id, post_id, csrf_token, cookies, time_period):
        """Retrieve user IDs of students who participated in a specific Piazza post"""
        request_data = {
            "method": "content.get",
            "params": {
                "cid": class_id,
                "nid": str(post_id),
                "student_view": None
            }
        }

        try:
            response = self.make_piazza_request(csrf_token, cookies, request_data)

            # Check if response contains expected data
            if 'result' not in response:
                self.log_message(f"WARNING: Unexpected response format for post {post_id}")
                return [], []

            if 'change_log' not in response['result']:
                self.log_message(f"WARNING: No change_log found for post {post_id}")
                return [], []

            change_log = response['result']['change_log']

            user_ids = set()
            late_user_ids = set()
            for log_entry in change_log:
                if 'when' in log_entry and 'uid' in log_entry:
                    if self.is_timestamp_in_period(log_entry['when'], time_period[0], time_period[1]):
                        user_ids.add(log_entry['uid'])
                    else:
                        late_user_ids.add(log_entry['uid'])

            return list(user_ids), list(late_user_ids - user_ids)

        except requests.exceptions.RequestException as e:
            self.log_message(f"ERROR: Network error for post {post_id} - {e}")
            return None, None
        except KeyError as e:
            self.log_message(f"ERROR: Unexpected data structure for post {post_id} - {e}")
            return None, None
        except Exception as e:
            self.log_message(f"ERROR: Failed to get user IDs for post {post_id} - {e}")
            return None, None

    def get_student_profile_data(self, user_id_list, class_id, csrf_token, cookies):
        """Retrieve profile data for a list of user IDs"""
        if not user_id_list:
            return None

        request_data = {
            "method": "network.get_users",
            "params": {
                "ids": user_id_list,
                "nid": class_id
            }
        }

        try:
            response = self.make_piazza_request(csrf_token, cookies, request_data)
            return response
        except Exception as e:
            self.log_message(f"ERROR: Failed to get student data - {e}")
            return None

    def extract_name_email_from_student_data(self, student_data):
        """Extract name and email from student profile data"""
        results = []
        if student_data and 'result' in student_data:
            for student in student_data['result']:
                if isinstance(student, dict) and student.get('role') == 'student':
                    name = student.get('name', 'Unknown')
                    email = student.get('email', '')
                    if email:  # Only add if email exists
                        results.append((name, email))
        return results

    def get_students_by_post(self, post_id, class_id, csrf_token, cookies, time_period):
        """Get list of students who participated in a single Piazza post"""
        try:
            user_ids, late_ids = self.get_user_ids_from_post(post_id, class_id, csrf_token, cookies, time_period)

            # Check if user_ids retrieval failed
            if user_ids is None:
                self.log_message(f"ERROR: Failed to get user IDs for post {post_id}")
                return None

            student_data = self.get_student_profile_data(user_ids, class_id, csrf_token, cookies)
            late_student_data = self.get_student_profile_data(late_ids, class_id, csrf_token, cookies)

            if late_student_data:
                late_students = self.extract_name_email_from_student_data(late_student_data)
                if late_students:
                    self.log_message(f"\n[Late Students in Post #{post_id}]:")
                    for ls in late_students:
                        self.log_message(f"  {ls[0]}")

            return self.extract_name_email_from_student_data(student_data)
        except Exception as e:
            self.log_message(f"ERROR: Failed to get students for post {post_id} - {e}")
            return None

    def get_students_by_lecture(self, start_post_id, end_post_id, class_id, csrf_token, cookies, time_period):
        """Get all students who participated in a lecture range of Piazza posts"""
        all_students = set()

        for post_id in range(start_post_id, end_post_id + 1):
            self.log_message(f"Processing post {post_id}...")
            students_in_post = self.get_students_by_post(str(post_id), class_id, csrf_token, cookies, time_period)

            # If any post returns None, it indicates an error
            if students_in_post is None:
                self.log_message(f"ERROR: Failed to process post {post_id}")
                return None

            if students_in_post:
                all_students.update(students_in_post)

        return list(all_students)

    def get_lecture_time_utc(self, section_number, lecture_date, start_time, end_time):
        """Get the UTC time for a given lecture with custom time frame"""
        try:
            start_datetime = f"{lecture_date} {start_time}:00"
            end_datetime = f"{lecture_date} {end_time}:00"

            # Check if end time is earlier than start time (crosses midnight)
            start_parsed = datetime.strptime(start_time, '%H:%M')
            end_parsed = datetime.strptime(end_time, '%H:%M')
            if end_parsed < start_parsed:
                # Adjust end date to next day
                next_day = (datetime.strptime(lecture_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
                end_datetime = f"{next_day} {end_time}:00"

            return (self.convert_chicago_to_utc(start_datetime),
                   self.convert_chicago_to_utc(end_datetime))
        except Exception as e:
            self.log_message(f"ERROR: Failed to calculate lecture time - {e}")
            return (None, None)

    def convert_chicago_to_utc(self, chicago_time_str):
        """Convert time from Chicago time to UTC time zone"""
        try:
            chicago_tz = pytz.timezone('America/Chicago')
            naive_time = datetime.strptime(chicago_time_str, '%Y-%m-%d %H:%M:%S')
            chicago_time = chicago_tz.localize(naive_time)
            utc_time = chicago_time.astimezone(pytz.UTC)
            return utc_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        except Exception as e:
            return f"Time conversion error: {e}"

    def is_timestamp_in_period(self, timestamp, period_start, period_end):
        """Check if a given UTC timestamp falls in a time period"""
        def parse_iso_time(time_str):
            if time_str.endswith('Z'):
                time_str = time_str.replace('Z', '+00:00')
            dt = datetime.fromisoformat(time_str)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=pytz.UTC)
            return dt

        try:
            dt = parse_iso_time(timestamp)
            start = parse_iso_time(period_start)
            end = parse_iso_time(period_end)

            dt_utc = dt.astimezone(pytz.UTC)
            start_utc = start.astimezone(pytz.UTC)
            end_utc = end.astimezone(pytz.UTC)

            return dt_utc <= end_utc
        except Exception as e:
            self.log_message(f"WARNING: Failed to parse timestamp: {e}")
            return False

    def process_student_participation(self, input_csv_path, student_list, lecture_number, output_csv_path):
        """Process student participation data and update Canvas grade CSV"""
        # Create output directory if needed
        output_directory = os.path.dirname(output_csv_path)
        if output_directory and not os.path.exists(output_directory):
            try:
                os.makedirs(output_directory)
                self.log_message(f"Created output directory: {output_directory}")
            except Exception as e:
                self.log_message(f"ERROR: Failed to create directory '{output_directory}' - {e}")
                return None

        # Load Canvas CSV data
        try:
            grade_data = pd.read_csv(input_csv_path)
            self.log_message(f"Loaded Canvas CSV with {len(grade_data)} students")
        except Exception as e:
            self.log_message(f"ERROR: Failed to read CSV file - {e}")
            return None

        # Check if required columns exist
        if 'SIS Login ID' not in grade_data.columns:
            self.log_message("ERROR: CSV file missing 'SIS Login ID' column")
            return None

        # Initialize participation column
        participation_column = f'Lec {lecture_number} Participation'
        grade_data[participation_column] = 0

        # Track unmatched students
        unmatched_students = []
        matched_count = 0

        # Update participation scores
        for name, email in student_list:
            try:
                uid = email.split('@')[0]
                if uid in grade_data['SIS Login ID'].values:
                    grade_data.loc[grade_data['SIS Login ID'] == uid, participation_column] = 50
                    matched_count += 1
                else:
                    unmatched_students.append((name, email))
            except Exception as e:
                self.log_message(f"WARNING: Failed to process student {name}: {e}")
                unmatched_students.append((name, email))

        # Report results
        self.log_message(f"\nMatched: {matched_count} students")
        self.log_message(f"Unmatched: {len(unmatched_students)} students")

        # Report unmatched students
        if unmatched_students:
            self.log_message("\n" + "=" * 50)
            self.log_message("UNMATCHED STUDENTS:")
            self.log_message("=" * 50)
            for student in unmatched_students[:20]:  # Show first 20
                self.log_message(f"  • {student[0]} ({student[1]})")
            if len(unmatched_students) > 20:
                self.log_message(f"  ... and {len(unmatched_students)-20} more")
            self.log_message("=" * 50)
        else:
            self.log_message("\n✓ All students matched successfully.")

        # Save to CSV
        try:
            grade_data.to_csv(output_csv_path, index=False, quoting=csv.QUOTE_MINIMAL)
            self.log_message(f"\n✓ Data saved to {output_csv_path}")
            return unmatched_students
        except Exception as e:
            self.log_message(f"ERROR: Failed to save CSV file - {e}")
            return None


def main():
    """Main function to run the Tkinter application"""
    root = tk.Tk()
    app = PiazzaGraderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
