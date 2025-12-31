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
import shutil

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
        self.log_file_path = "log.txt"
        self.stop_logging = False

        # Task checkboxes storage
        self.task_vars = {}
        self.task_checkboxes = []

        # Anchor project root (CLI-equivalent)
        self.project_root = Path.cwd().resolve()

        self.create_widgets()
        self.load_tasks()

    # ---------------- UI SETUP ----------------

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)

        ttk.Label(main_frame, text="Vehicle Serial:").grid(row=0, column=0, sticky=tk.W)
        serial_frame = ttk.Frame(main_frame)
        serial_frame.grid(row=0, column=1, sticky=tk.W)

        ttk.Label(serial_frame, textvariable=self.vehicle_serial,
                  font=('TkDefaultFont', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        ttk.Button(serial_frame, text="Get Serial Number",
                   command=self.get_serial_number).pack(side=tk.LEFT)

        ttk.Label(main_frame, text="Truck Type:").grid(row=1, column=0, sticky=tk.W)
        truck_frame = ttk.Frame(main_frame)
        truck_frame.grid(row=1, column=1, sticky=tk.W)

        ttk.Radiobutton(truck_frame, text="RS1", variable=self.truck_type,
                        value="RS1", command=self.load_tasks).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(truck_frame, text="CR1", variable=self.truck_type,
                        value="CR1", command=self.load_tasks).pack(side=tk.LEFT, padx=10)

        ttk.Label(main_frame, text="Load Status:").grid(row=2, column=0, sticky=tk.W)
        load_frame = ttk.Frame(main_frame)
        load_frame.grid(row=2, column=1, sticky=tk.W)

        ttk.Radiobutton(load_frame, text="Unloaded",
                        variable=self.load_status, value="Unloaded").pack(side=tk.LEFT)
        ttk.Radiobutton(load_frame, text="Loaded",
                        variable=self.load_status, value="Loaded").pack(side=tk.LEFT)

        ttk.Label(main_frame, text="Repeat Count:").grid(row=2, column=2, sticky=tk.W)
        ttk.Combobox(main_frame, textvariable=self.repeat_count,
                     values=[1, 2, 3, 4, 5],
                     state="readonly", width=10).grid(row=2, column=3)

        ttk.Label(main_frame, text="Select Tasks:").grid(row=3, column=0, sticky=tk.NW)

        container = ttk.Frame(main_frame)
        container.grid(row=3, column=1, sticky="nsew")

        canvas = tk.Canvas(container, height=150)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.task_frame = ttk.Frame(canvas)

        self.task_frame.bind("<Configure>",
                             lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=self.task_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(main_frame, text="Test Log:").grid(row=4, column=0, sticky=tk.NW)
        self.log_text = scrolledtext.ScrolledText(main_frame, height=15, state="disabled")
        self.log_text.grid(row=4, column=1, sticky="nsew")

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2)

        self.start_btn = ttk.Button(button_frame, text="Start Test",
                                    command=self.start_test)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(button_frame, text="Stop Test",
                                   command=self.stop_test, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="Clear Log",
                   command=self.clear_log).pack(side=tk.LEFT)

    # ---------------- TASK HANDLING ----------------

    def load_tasks(self):
        for widget in self.task_frame.winfo_children():
            widget.destroy()
        self.task_vars.clear()

        project_file = self.project_root / f"{self.truck_type.get()}_project.yml"
        if not project_file.exists():
            ttk.Label(self.task_frame, text=f"{project_file} not found").pack()
            return

        with open(project_file, "r") as f:
            data = yaml.safe_load(f)

        for task in data.get("Tasks", []):
            name = task.get("Name", "")
            if "initialize" in name.lower() or "process" in name.lower():
                continue
            var = tk.BooleanVar(value=True)
            self.task_vars[name] = var
            ttk.Checkbutton(self.task_frame, text=name, variable=var).pack(anchor=tk.W)

    # ---------------- SERIAL ----------------

    def get_serial_number(self):
        threading.Thread(target=self._get_serial_number_thread, daemon=True).start()

    def _get_serial_number_thread(self):
        try:
            from remote_ctrl.remote_ssh_2 import RemoteSSH
            project_file = self.project_root / f"{self.truck_type.get()}_project.yml"

            with open(project_file) as f:
                data = yaml.safe_load(f)

            remote = RemoteSSH(
                data.get("PassWordRequired", False),
                data.get("IPAddress", "10.0.0.2"),
                data.get("IsHardWired", True),
                data.get("StepPause_sec", 1)
            )

            info = remote.GetVehicleName()
            match = re.search(r"VEH NAME:\s*(\S+)", info)
            serial = match.group(1) if match else "Parse Error"

            self.root.after(0, lambda: self.vehicle_serial.set(serial))
            self.root.after(0, lambda: self.log_message(f"Serial: {serial}"))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))

    # ---------------- RUN TEST ----------------

    def start_test(self):
        if self.vehicle_serial.get() == "Not Retrieved":
            messagebox.showwarning("Warning", "Get serial first")
            return

        selected = [k for k, v in self.task_vars.items() if v.get()]
        if not selected:
            messagebox.showwarning("Warning", "Select tasks")
            return

        output_dir = (
            Path("results")
            / self.truck_type.get().lower()
            / self.vehicle_serial.get()
            / self.load_status.get()
            / datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        self.create_temp_project_file(selected, output_dir)

        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

        threading.Thread(target=self.run_test, args=(output_dir,), daemon=True).start()
        threading.Thread(target=self.monitor_log, daemon=True).start()

    def create_temp_project_file(self, tasks, output_dir):
        project_file = self.project_root / f"{self.truck_type.get()}_project.yml"
        with open(project_file) as f:
            data = yaml.safe_load(f)

        filtered = []
        for t in data["Tasks"]:
            name = t.get("Name", "")
            if "initialize" in name.lower():
                filtered.append(t)
            elif name in tasks:
                t2 = t.copy()
                t2["Repeat"] = self.repeat_count.get()
                filtered.append(t2)

        data["Tasks"] = filtered
        with open(output_dir / "project.yml", "w") as f:
            yaml.dump(data, f)

    def run_test(self, output_dir):
        try:
            cmd = [
                "python3",
                str(self.project_root / "RunHydCommands.py"),
                "-p",
                str(output_dir / "project.yml")
            ]

            self.running_process = subprocess.Popen(
                cmd,
                cwd=self.project_root,   # CLI-equivalent cwd
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            self.running_process.wait()

            # ⭐ GUI-only fix: relocate outputs
            self.relocate_outputs(output_dir)

            if self.running_process.returncode == 0:
                self.log_message("Test completed successfully")
                self.log_message(f"Results saved to: {output_dir}")
            else:
                self.log_message(f"Test failed (code {self.running_process.returncode})")

        except Exception as e:
            self.log_message(f"Error running test: {e}")

        finally:
            self.running_process = None
            self.stop_logging = True
            self.root.after(0, lambda: self.start_btn.config(state="normal"))
            self.root.after(0, lambda: self.stop_btn.config(state="disabled"))

    # ---------------- OUTPUT RELOCATION ----------------

    def relocate_outputs(self, output_dir):
        artifacts = [
            "out.txt",
            "post_out.txt",
            "results.txt",
            "results.csv",
            "ServoLogs"
        ]

        for name in artifacts:
            src = self.project_root / name
            if not src.exists():
                continue

            dst = output_dir / name

            try:
                if dst.exists():
                    if dst.is_dir():
                        shutil.rmtree(dst)
                    else:
                        dst.unlink()

                shutil.move(str(src), str(dst))
                self.log_message(f"Moved {name} → {dst}")

            except Exception as e:
                self.log_message(f"WARNING: Failed to move {name}: {e}")

    # ---------------- LOGGING ----------------

    def monitor_log(self):
        if not os.path.exists(self.log_file_path):
            return

        with open(self.log_file_path) as f:
            f.seek(0, 2)
            while not self.stop_logging:
                line = f.readline()
                if line:
                    self.root.after(0, lambda l=line: self.log_message(l.strip()))
                else:
                    time.sleep(0.1)

    def log_message(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def stop_test(self):
        if self.running_process:
            self.running_process.terminate()

    def clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")


def main():
    root = tk.Tk()
    HydraulicTestGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
