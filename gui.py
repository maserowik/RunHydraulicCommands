import tkinter as tk
from tkinter import scrolledtext
import threading
import subprocess
import sys
import os
import re

class RobotTestGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Robot Hydraulic Test")

        # --- Top panel: Robot and Load State ---
        top_frame = tk.Frame(root)
        top_frame.pack(pady=5, fill="x")

        # Robot selection
        robot_frame = tk.LabelFrame(top_frame, text="Select Robot", padx=10, pady=5)
        robot_frame.pack(side="left", padx=10)
        self.robot_var = tk.StringVar(value="RS1")
        tk.Radiobutton(robot_frame, text="RS1", variable=self.robot_var, value="RS1").pack(side="left", padx=5)
        tk.Radiobutton(robot_frame, text="CR1", variable=self.robot_var, value="CR1").pack(side="left", padx=5)

        # Load state
        load_frame = tk.LabelFrame(top_frame, text="Select Test Mode", padx=10, pady=5)
        load_frame.pack(side="left", padx=10)
        self.load_var = tk.StringVar(value="Loaded")
        tk.Radiobutton(load_frame, text="Unloaded", variable=self.load_var, value="Unloaded").pack(side="left", padx=5)
        tk.Radiobutton(load_frame, text="Loaded", variable=self.load_var, value="Loaded").pack(side="left", padx=5)

        # --- Test Log ---
        log_frame = tk.LabelFrame(root, text="Test Log", padx=5, pady=5)
        log_frame.pack(pady=5, fill="both", expand=True)
        self.log_box = scrolledtext.ScrolledText(log_frame, width=80, height=15, state="disabled")
        self.log_box.pack(fill="both", expand=True)

        # --- Results info ---
        results_frame = tk.LabelFrame(root, text="Results Saved to:", padx=5, pady=5)
        results_frame.pack(fill="x", padx=5, pady=2)
        self.results_label = tk.Label(results_frame, text="results/N/A")
        self.results_label.pack(anchor="w")

        # --- Buttons ---
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)
        self.start_btn = tk.Button(btn_frame, text="Start Test", bg="#007ACC", fg="white", width=15, command=self.start_test)
        self.start_btn.pack(side="left", padx=10)
        self.stop_btn = tk.Button(btn_frame, text="Stop Test", bg="#D9534F", fg="white", width=15, command=self.stop_test, state="disabled")
        self.stop_btn.pack(side="left", padx=10)

        # --- Serial number and project file handling ---
        self.robot_serials = {}  # {robot_name: serial_number}
        self.serial_counter = 1
        self.project_files = {
            "RS1": "rs1_project.yml",
            "CR1": "cr1_project.yaml"
        }

        # Process handling
        self.process = None
        self.stop_flag = threading.Event()
        self.serial_number = "N/A"

    # --- Generate or retrieve serial number ---
    def get_serial_for_robot(self, robot):
        if robot not in self.robot_serials:
            serial = f"SN{self.serial_counter:04d}"
            self.robot_serials[robot] = serial
            self.serial_counter += 1
        return self.robot_serials[robot]

    # --- Create results folder and placeholder files ---
    def prepare_results_folder(self, robot, serial, load_type):
        folder_path = os.path.join("results", robot, serial, load_type)
        os.makedirs(folder_path, exist_ok=True)
        for fname in ["out.txt", "post_out.txt", "results.txt", "results.csv"]:
            file_path = os.path.join(folder_path, fname)
            if not os.path.exists(file_path):
                with open(file_path, "w") as f:
                    f.write("")  # empty placeholder
        return folder_path

    # --- Start test ---
    def start_test(self):
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.clear_log()

        robot = self.robot_var.get()
        load_type = self.load_var.get()
        self.serial_number = self.get_serial_for_robot(robot)

        results_folder = self.prepare_results_folder(robot, self.serial_number, load_type)
        self.update_results_label(robot, self.serial_number, load_type)

        self.stop_flag.clear()
        threading.Thread(target=self.run_command, args=(robot, load_type, results_folder), daemon=True).start()

    # --- Stop test ---
    def stop_test(self):
        self.stop_flag.set()
        if self.process and self.process.poll() is None:
            self.process.terminate()
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.append_log("Test stopped by user.\n")

    # --- Run external Python command ---
    def run_command(self, robot, load_type, results_folder):
        project_file = self.project_files.get(robot)
        cmd = [
            sys.executable,
            os.path.join(os.getcwd(), "RunHydCommands.py"),
            robot,
            load_type,
            "-p", project_file,
            "-r", results_folder
        ]

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            for line in self.process.stdout:
                if self.stop_flag.is_set():
                    break
                self.append_log(line)
                self.check_serial_number(line)
            self.process.wait()
        except Exception as e:
            self.append_log(f"Error: {e}\n")
        finally:
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")

    # --- Optional: detect serial number from output ---
    def check_serial_number(self, line):
        match = re.search(r"Serial Number:\s*(\S+)", line)
        if match:
            self.serial_number = match.group(1)
            self.update_results_label(self.robot_var.get(), self.serial_number, self.load_var.get())

    # --- Update results label ---
    def update_results_label(self, robot, serial, load_type):
        self.results_label.config(text=f"results/{robot}/{serial}/{load_type}")

    # --- Append to log box ---
    def append_log(self, text):
        self.log_box.config(state="normal")
        self.log_box.insert(tk.END, text)
        self.log_box.see(tk.END)
        self.log_box.config(state="disabled")

    # --- Clear log box ---
    def clear_log(self):
        self.log_box.config(state="normal")
        self.log_box.delete(1.0, tk.END)
        self.log_box.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = RobotTestGUI(root)
    root.mainloop()
