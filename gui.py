import tkinter as tk
from tkinter import scrolledtext
import threading
import subprocess
import yaml
import os
import sys

class RobotTestGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Robot Hydraulic Test")

        # --- Serial number tracking ---
        self.serial_counter = 1

        # --- Robot selection ---
        top_frame = tk.Frame(root)
        top_frame.pack(pady=5, fill="x")

        robot_frame = tk.LabelFrame(top_frame, text="Select Robot", padx=10, pady=5)
        robot_frame.pack(side="left", padx=10)
        self.robot_var = tk.StringVar(value="RS1")
        tk.Radiobutton(robot_frame, text="RS1", variable=self.robot_var, value="RS1", command=self.update_tasks).pack(side="left", padx=5)
        tk.Radiobutton(robot_frame, text="CR1", variable=self.robot_var, value="CR1", command=self.update_tasks).pack(side="left", padx=5)

        load_frame = tk.LabelFrame(top_frame, text="Select Test Mode", padx=10, pady=5)
        load_frame.pack(side="left", padx=10)
        self.load_var = tk.StringVar(value="Loaded")
        tk.Radiobutton(load_frame, text="Unloaded", variable=self.load_var, value="Unloaded", command=self.update_tasks).pack(side="left", padx=5)
        tk.Radiobutton(load_frame, text="Loaded", variable=self.load_var, value="Loaded", command=self.update_tasks).pack(side="left", padx=5)

        # --- Task selection ---
        task_frame = tk.LabelFrame(root, text="Select Tasks to Run", padx=5, pady=5)
        task_frame.pack(fill="both", padx=5, pady=5)
        self.task_vars = {}
        self.task_checks = []
        self.task_frame = task_frame

        self.select_all_var = tk.BooleanVar(value=True)
        select_all_cb = tk.Checkbutton(task_frame, text="Select All", variable=self.select_all_var, command=self.toggle_all_tasks)
        select_all_cb.pack(anchor="w")

        # --- Test log ---
        log_frame = tk.LabelFrame(root, text="Test Log", padx=5, pady=5)
        log_frame.pack(pady=5, fill="both", expand=True)
        self.log_box = scrolledtext.ScrolledText(log_frame, width=80, height=15)
        self.log_box.pack(fill="both", expand=True)

        # --- Results folder info ---
        results_frame = tk.LabelFrame(root, text="Results Folder", padx=5, pady=5)
        results_frame.pack(fill="x", padx=5, pady=2)
        self.results_label = tk.Label(results_frame, text="results/")
        self.results_label.pack(anchor="w")

        # --- Buttons ---
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)
        self.start_btn = tk.Button(btn_frame, text="Start Test", bg="#007ACC", fg="white", width=15, command=self.start_test)
        self.start_btn.pack(side="left", padx=10)
        self.stop_btn = tk.Button(btn_frame, text="Stop Test", bg="#D9534F", fg="white", width=15, command=self.stop_test)
        self.stop_btn.pack(side="left", padx=10)
        self.clear_btn = tk.Button(btn_frame, text="Clear Log", bg="#6c757d", fg="white", width=15, command=self.clear_log)
        self.clear_btn.pack(side="left", padx=10)

        # Thread control
        self.process = None
        self.stop_flag = threading.Event()

        # Load initial tasks
        self.update_tasks()

    # ---------------------------
    # Helper functions
    # ---------------------------

    def append_log(self, text):
        self.log_box.insert(tk.END, text)
        self.log_box.see(tk.END)

    def clear_log(self):
        self.log_box.delete(1.0, tk.END)

    def toggle_all_tasks(self):
        for var in self.task_vars.values():
            var.set(self.select_all_var.get())

    def update_tasks(self):
        # Clear old tasks
        for chk in self.task_checks:
            chk.destroy()
        self.task_vars.clear()
        self.task_checks.clear()

        robot = self.robot_var.get()
        project_file = f"{robot}_project.yml"
        if not os.path.exists(project_file):
            self.append_log(f"Project file not found: {project_file}\n")
            return

        with open(project_file, "r") as f:
            try:
                project_data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                self.append_log(f"YAML parse error: {e}\n")
                return

        tasks = project_data.get("Tasks", [])
        # Filter out post-process tasks
        gui_tasks = [t for t in tasks if "Process" not in t["Name"]]

        for task in gui_tasks:
            name = task["Name"]
            var = tk.BooleanVar(value=True)
            cb = tk.Checkbutton(self.task_frame, text=name, variable=var)
            cb.pack(anchor="w")
            self.task_vars[name] = var
            self.task_checks.append(cb)

        # Update results folder path
        serial = f"SN{self.serial_counter:04d}"
        load = self.load_var.get()
        results_folder = os.path.join("results", robot, serial, load)
        os.makedirs(results_folder, exist_ok=True)
        self.results_label.config(text=results_folder)

    # ---------------------------
    # Start / Stop
    # ---------------------------

    def start_test(self):
        selected_tasks = [name for name, var in self.task_vars.items() if var.get()]
        if not selected_tasks:
            self.append_log("ERROR: No tasks selected.\n")
            return

        robot = self.robot_var.get()
        load = self.load_var.get()
        serial = f"SN{self.serial_counter:04d}"
        results_folder = os.path.join("results", robot, serial, load)
        os.makedirs(results_folder, exist_ok=True)
        self.results_label.config(text=results_folder)

        project_file = f"{robot}_project.yml"
        with open(project_file, "r") as f:
            project_data = yaml.safe_load(f)

        # Filter tasks for selected tasks only (GUI) but keep post-process
        filtered_tasks = [t for t in project_data.get("Tasks", []) if ("Process" in t["Name"] or t["Name"] in selected_tasks)]
        filtered_data = project_data.copy()
        filtered_data["Tasks"] = filtered_tasks

        temp_yaml = os.path.join(results_folder, "temp_project.yml")
        with open(temp_yaml, "w") as f:
            yaml.safe_dump(filtered_data, f)

        # Run in a thread
        self.stop_flag.clear()
        threading.Thread(target=self.run_tasks, args=(temp_yaml, robot, load, results_folder), daemon=True).start()

    def run_tasks(self, temp_yaml, robot, load, results_folder):
        cmd = [
            sys.executable,
            os.path.join(os.getcwd(), "RunHydCommands.py"),
            robot,
            load,
            "-p", temp_yaml,
            "-r", results_folder
        ]
        self.append_log(f"Running command: {' '.join(cmd)}\n")
        try:
            self.process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
            )
            for line in self.process.stdout:
                if self.stop_flag.is_set():
                    self.process.terminate()
                    self.append_log("Test stopped by user.\n")
                    return
                self.append_log(line)
            self.process.wait()
            self.append_log("Test completed.\n")
        except Exception as e:
            self.append_log(f"Error running test: {e}\n")

    def stop_test(self):
        self.stop_flag.set()
        if self.process:
            self.process.terminate()
            self.append_log("Stopping test...\n")

# ---------------------------
# Main
# ---------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = RobotTestGUI(root)
    root.mainloop()
