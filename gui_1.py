#!/usr/bin/env python3
"""
Hydraulic Automated Testing Tool - GUI
Wrapper for RunHydCommands.py - does not modify base code
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import yaml
import os
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
import re

class HydraulicTestGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Hydraulic Automated Testing Tool")
        self.root.geometry("900x700")
        
        # State variables
        self.vehicle_serial = tk.StringVar(value="Not Retrieved")
        self.truck_type = tk.StringVar(value="RS1")
        self.load_status = tk.StringVar(value="Unloaded")
        self.repeat_count = tk.IntVar(value=1)
        self.running_process = None
        self.stop_logging = False
        
        # Task checkboxes storage
        self.task_vars = {}
        self.task_checkboxes = []
        
        self.create_widgets()
        self.load_tasks()
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # --- Row 0: Vehicle Serial ---
        ttk.Label(main_frame, text="Vehicle Serial:").grid(row=0, column=0, sticky=tk.W, pady=5)
        serial_frame = ttk.Frame(main_frame)
        serial_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(serial_frame, textvariable=self.vehicle_serial, font=('TkDefaultFont', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        ttk.Button(serial_frame, text="Get Serial Number", command=self.get_serial_number).pack(side=tk.LEFT, padx=5)
        
        # --- Row 1: Truck Type ---
        ttk.Label(main_frame, text="Truck Type:").grid(row=1, column=0, sticky=tk.W, pady=5)
        truck_frame = ttk.Frame(main_frame)
        truck_frame.grid(row=1, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(truck_frame, text="RS1", variable=self.truck_type, value="RS1", command=self.load_tasks).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(truck_frame, text="CR1", variable=self.truck_type, value="CR1", command=self.load_tasks).pack(side=tk.LEFT, padx=10)
        
        # --- Row 2: Load Status ---
        ttk.Label(main_frame, text="Load Status:").grid(row=2, column=0, sticky=tk.W, pady=5)
        load_frame = ttk.Frame(main_frame)
        load_frame.grid(row=2, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(load_frame, text="Unloaded", variable=self.load_status, value="Unloaded").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(load_frame, text="Loaded", variable=self.load_status, value="Loaded").pack(side=tk.LEFT, padx=10)
        
        # --- Row 2b: Repeat Count ---
        ttk.Label(main_frame, text="Repeat Count:").grid(row=2, column=2, sticky=tk.W, pady=5, padx=(20,0))
        repeat_combo = ttk.Combobox(main_frame, textvariable=self.repeat_count, values=[1,2,3,4,5], state='readonly', width=10)
        repeat_combo.grid(row=2, column=3, sticky=tk.W, pady=5)
        repeat_combo.current(0)
        
        # --- Row 3: Tasks ---
        ttk.Label(main_frame, text="Select Tasks:").grid(row=3, column=0, sticky=(tk.W, tk.N), pady=5)
        task_container = ttk.Frame(main_frame)
        task_container.grid(row=3, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        task_canvas = tk.Canvas(task_container, height=150)
        task_scrollbar = ttk.Scrollbar(task_container, orient="vertical", command=task_canvas.yview)
        self.task_frame = ttk.Frame(task_canvas)
        self.task_frame.bind("<Configure>", lambda e: task_canvas.configure(scrollregion=task_canvas.bbox("all")))
        task_canvas.create_window((0,0), window=self.task_frame, anchor="nw")
        task_canvas.configure(yscrollcommand=task_scrollbar.set)
        task_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        task_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # --- Row 4: Log ---
        ttk.Label(main_frame, text="Test Log:").grid(row=4, column=0, sticky=(tk.W, tk.N), pady=5)
        self.log_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=15, state='disabled')
        self.log_text.grid(row=4, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # --- Row 5: Buttons ---
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        self.start_btn = ttk.Button(button_frame, text="Start Test", command=self.start_test, width=15)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = ttk.Button(button_frame, text="Stop Test", command=self.stop_test, state='disabled', width=15)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Log", command=self.clear_log, width=15).pack(side=tk.LEFT, padx=5)
    
    def load_tasks(self):
        for widget in self.task_frame.winfo_children():
            widget.destroy()
        self.task_vars.clear()
        self.task_checkboxes.clear()
        
        truck_type = self.truck_type.get()
        project_file = f"{truck_type}_project.yml"
        if not os.path.exists(project_file):
            ttk.Label(self.task_frame, text=f"Error: {project_file} not found!").pack()
            return
        try:
            with open(project_file, 'r') as f:
                project_data = yaml.safe_load(f)
            if 'Tasks' not in project_data:
                ttk.Label(self.task_frame, text="No tasks found in project file").pack()
                return
            for task in project_data['Tasks']:
                task_name = task.get('Name','')
                if 'initialize' in task_name.lower() or 'process' in task_name.lower():
                    continue
                var = tk.BooleanVar(value=True)
                self.task_vars[task_name] = var
                cb = ttk.Checkbutton(self.task_frame, text=task_name, variable=var)
                cb.pack(anchor=tk.W, padx=5, pady=2)
                self.task_checkboxes.append(cb)
            # Select/deselect all
            btn_frame = ttk.Frame(self.task_frame)
            btn_frame.pack(anchor=tk.W, padx=5, pady=5)
            ttk.Button(btn_frame, text="Select All", command=self.select_all_tasks).pack(side=tk.LEFT, padx=2)
            ttk.Button(btn_frame, text="Deselect All", command=self.deselect_all_tasks).pack(side=tk.LEFT, padx=2)
        except Exception as e:
            ttk.Label(self.task_frame, text=f"Error loading tasks: {str(e)}").pack()
    
    def select_all_tasks(self):
        for var in self.task_vars.values():
            var.set(True)
    
    def deselect_all_tasks(self):
        for var in self.task_vars.values():
            var.set(False)
    
    def get_serial_number(self):
        self.log_message("Retrieving vehicle serial number...")
        threading.Thread(target=self._get_serial_number_thread, daemon=True).start()
    
    def _get_serial_number_thread(self):
        try:
            from remote_ctrl.remote_ssh_2 import RemoteSSH
            truck_type = self.truck_type.get()
            project_file = f"{truck_type}_project.yml"
            with open(project_file, 'r') as f:
                project_data = yaml.safe_load(f)
            ip_address = project_data.get('IPAddress', '10.0.0.2')
            password_required = project_data.get('PassWordRequired', False)
            is_hardwired = project_data.get('IsHardWired', True)
            step_pause = project_data.get('StepPause_sec', 1)
            remote = RemoteSSH(password_required, ip_address, is_hardwired, step_pause)
            vehicle_info = remote.GetVehicleName()
            match = re.search(r'VEH NAME:\s*(\S+)', vehicle_info)
            if match:
                serial = match.group(1).strip()
                self.root.after(0, lambda: self.vehicle_serial.set(serial))
                self.root.after(0, lambda: self.log_message(f"Serial number retrieved: {serial}"))
            else:
                self.root.after(0, lambda: self.vehicle_serial.set("Parse Error"))
                self.root.after(0, lambda: self.log_message(f"Could not parse serial from: {vehicle_info}"))
        except Exception as e:
            self.root.after(0, lambda: self.vehicle_serial.set("Error"))
            self.root.after(0, lambda: self.log_message(f"Error retrieving serial: {str(e)}"))
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to get serial number:\n{str(e)}"))
    
    def start_test(self):
        if self.vehicle_serial.get() == "Not Retrieved":
            messagebox.showwarning("Warning", "Please retrieve vehicle serial number first")
            return
        selected_tasks = [name for name, var in self.task_vars.items() if var.get()]
        if not selected_tasks:
            messagebox.showwarning("Warning", "Please select at least one task")
            return
        truck_type = self.truck_type.get().lower()
        serial = self.vehicle_serial.get()
        load_status = self.load_status.get()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("results") / truck_type / serial / load_status / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)
        self.log_message(f"Output directory: {output_dir}")
        self.log_message(f"Selected tasks: {', '.join(selected_tasks)}")
        self.log_message(f"Repeat count: {self.repeat_count.get()}")
        self.create_temp_project_file(selected_tasks, output_dir)
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        threading.Thread(target=self.run_test, args=(output_dir,), daemon=True).start()
    
    def create_temp_project_file(self, selected_tasks, output_dir):
        truck_type = self.truck_type.get()
        project_file = f"{truck_type}_project.yml"
        repeat_count = self.repeat_count.get()
        with open(project_file, 'r') as f:
            project_data = yaml.safe_load(f)
        filtered_tasks = []
        for task in project_data['Tasks']:
            task_name = task.get('Name','')
            if 'initialize' in task_name.lower():
                filtered_tasks.append(task)
                continue
            if task_name in selected_tasks:
                task_copy = task.copy()
                task_copy['Repeat'] = repeat_count
                filtered_tasks.append(task_copy)
                continue
            if 'Process' in task_name:
                base_name = task_name.replace('Process.yml','.yml')
                if base_name in selected_tasks:
                    filtered_tasks.append(task)
        project_data['Tasks'] = filtered_tasks
        temp_project = output_dir / "project.yml"
        with open(temp_project, 'w') as f:
            yaml.dump(project_data, f, default_flow_style=False)
        self.temp_project_file = str(temp_project)
    
    def run_test(self, output_dir):
        """Run hydraulic test and ensure all critical files go into output_dir"""
        try:
            script_path = os.path.abspath('RunHydCommands.py')
            temp_project_file = os.path.abspath(self.temp_project_file)
            cmd = ['python3', script_path, '-p', temp_project_file]

            original_dir = os.getcwd()

            self.running_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=original_dir
            )

            # Real-time GUI logging
            for line in self.running_process.stdout:
                self.root.after(0, lambda l=line: self.log_message(l.strip()))

            self.running_process.wait()

            # Move critical files
            critical_files = ["out.txt", "post_out.txt", "results.csv", "results.txt"]
            missing_files = []
            for f in critical_files:
                src = Path(original_dir) / f
                dest = Path(output_dir) / f
                if src.exists():
                    src.rename(dest)
                    self.log_message(f"Moved {f} to output folder")
                else:
                    missing_files.append(f)
            if missing_files:
                self.log_message(f"WARNING: Missing critical files: {', '.join(missing_files)}")

            if self.running_process.returncode == 0:
                self.log_message("Test completed successfully!")
                self.log_message(f"Results saved to: {output_dir}")
            else:
                self.log_message(f"Test failed with return code: {self.running_process.returncode}")

        except Exception as e:
            self.log_message(f"Error running test: {str(e)}")
        finally:
            self.running_process = None
            self.stop_logging = True
            self.root.after(0, lambda: self.start_btn.config(state='normal'))
            self.root.after(0, lambda: self.stop_btn.config(state='disabled'))
    
    def stop_test(self):
        if self.running_process:
            self.log_message("Stopping test...")
            self.running_process.terminate()
            time.sleep(1)
            if self.running_process.poll() is None:
                self.running_process.kill()
            self.stop_logging = True
            self.log_message("Test stopped")
            self.start_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
    
    def log_message(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + '\n')
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def clear_log(self):
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')


def main():
    root = tk.Tk()
    app = HydraulicTestGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
