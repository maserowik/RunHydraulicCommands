#!/usr/bin/env python3
"""
Hydraulic Automated Testing Tool - GUI
Wrapper for RunHydCommands.py - does not modify base code
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
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
        self.root.geometry("900x750")

        # ---------------- State ----------------
        self.vehicle_serial = tk.StringVar(value="Not Retrieved")
        self.truck_type = tk.StringVar(value="RS1")
        self.load_status = tk.StringVar(value="Unloaded")
        self.repeat_count = tk.IntVar(value=1)

        self.status_text = tk.StringVar(value="Status: Idle")
        self.eta_text = tk.StringVar(value="ETA: --")

        self.running_process = None

        self.task_vars = {}
        self.task_checkboxes = []
        self.selected_tasks = []
        self.completed_tasks = set()

        self.current_task = None
        self.task_start_time = None
        self.task_durations = []
        self.task_log_file = None

        # ---------------- GUI ----------------
        self.create_widgets()
        self.load_tasks()

        # ---------------- Styles ----------------
        style = ttk.Style()
        style.configure("NormalTask.TCheckbutton", background="")
        style.configure("RunningTask.TCheckbutton", background="#fff2a8")
        style.configure("CompletedTask.TCheckbutton", foreground="gray")

        # Example task → log matching rules
        self.task_log_patterns = {
            "Raise Boom": r"Raise Boom",
            "Lower Boom": r"Lower Boom",
            "Extend Arm": r"Extend Arm",
            "Retract Arm": r"Retract Arm",
        }

    # ------------------------------------------------------------------
    # GUI SETUP
    # ------------------------------------------------------------------

    def create_widgets(self):
        main = ttk.Frame(self.root, padding=10)
        main.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main.columnconfigure(1, weight=1)
        main.rowconfigure(4, weight=1)

        ttk.Label(main, text="Vehicle Serial:").grid(row=0, column=0, sticky="w")
        ttk.Label(main, textvariable=self.vehicle_serial, font=("TkDefaultFont", 10, "bold")).grid(row=0, column=1, sticky="w")

        ttk.Label(main, text="Truck Type:").grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(main, text="RS1", variable=self.truck_type, value="RS1", command=self.load_tasks).grid(row=1, column=1, sticky="w")
        ttk.Radiobutton(main, text="CR1", variable=self.truck_type, value="CR1", command=self.load_tasks).grid(row=1, column=1, padx=80, sticky="w")

        ttk.Label(main, text="Load Status:").grid(row=2, column=0, sticky="w")
        ttk.Radiobutton(main, text="Unloaded", variable=self.load_status, value="Unloaded").grid(row=2, column=1, sticky="w")
        ttk.Radiobutton(main, text="Loaded", variable=self.load_status, value="Loaded").grid(row=2, column=1, padx=80, sticky="w")

        ttk.Label(main, text="Select Tasks:").grid(row=3, column=0, sticky="nw")
        task_container = ttk.Frame(main)
        task_container.grid(row=3, column=1, sticky="nsew")

        canvas = tk.Canvas(task_container, height=150)
        scrollbar = ttk.Scrollbar(task_container, orient="vertical", command=canvas.yview)
        self.task_frame = ttk.Frame(canvas)

        self.task_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.task_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        ttk.Label(main, text="Test Log:").grid(row=4, column=0, sticky="nw")
        self.log_text = scrolledtext.ScrolledText(main, height=15, state="disabled")
        self.log_text.grid(row=4, column=1, sticky="nsew")

        # ETA
        ttk.Label(main, textvariable=self.eta_text).grid(row=5, column=1, sticky="e", padx=10)

        # Progress Bar
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(main, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=6, column=0, columnspan=2, sticky="ew", pady=5)

        # Buttons
        btns = ttk.Frame(main)
        btns.grid(row=7, column=0, columnspan=2, pady=10)

        self.start_btn = ttk.Button(btns, text="Start Test", command=self.start_test)
        self.start_btn.pack(side="left", padx=5)

        self.stop_btn = ttk.Button(btns, text="Stop Test", command=self.stop_test, state="disabled")
        self.stop_btn.pack(side="left", padx=5)

        ttk.Button(btns, text="Clear Log", command=self.clear_log).pack(side="left", padx=5)

        # Status Bar
        status = ttk.Label(self.root, textvariable=self.status_text, relief=tk.SUNKEN, anchor="w", padding=4)
        status.grid(row=1, column=0, sticky="ew")

    # ------------------------------------------------------------------
    # TASK SETUP
    # ------------------------------------------------------------------

    def load_tasks(self):
        for w in self.task_frame.winfo_children():
            w.destroy()

        self.task_vars.clear()
        self.task_checkboxes.clear()

        tasks = ["Raise Boom", "Lower Boom", "Extend Arm", "Retract Arm"]

        for task in tasks:
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(self.task_frame, text=task, variable=var, style="NormalTask.TCheckbutton")
            chk.pack(anchor="w", padx=5, pady=2)
            self.task_vars[task] = var
            self.task_checkboxes.append((task, chk))

    # ------------------------------------------------------------------
    # TEST CONTROL
    # ------------------------------------------------------------------

    def start_test(self):
        self.selected_tasks = [t for t, v in self.task_vars.items() if v.get()]
        if not self.selected_tasks:
            messagebox.showwarning("No Tasks", "Select at least one task.")
            return

        self.completed_tasks.clear()
        self.task_durations.clear()
        self.progress_var.set(0)

        output_dir = Path.cwd() / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_dir.mkdir(parents=True, exist_ok=True)

        self.task_log_file = output_dir / "task_timing.log"
        with open(self.task_log_file, "w") as f:
            f.write(f"Hydraulic Test Task Timing Log\nStarted: {datetime.now().isoformat()}\n\n")

        self.status_text.set("Status: Running")
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

        threading.Thread(target=self.run_test, args=(output_dir,), daemon=True).start()

    def run_test(self, output_dir):
        try:
            cmd = ["python3", "RunHydCommands.py"]
            self.running_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            for line in self.running_process.stdout:
                line = line.strip()
                self.root.after(0, lambda l=line: self.log_message(l))

                for task, pattern in self.task_log_patterns.items():
                    if re.search(pattern, line, re.IGNORECASE):
                        if task != self.current_task:
                            if self.current_task:
                                self.root.after(0, lambda t=self.current_task: self.set_task_completed(t))
                            self.root.after(0, lambda t=task: self.set_task_running(t))
                        break

            self.running_process.wait()

        finally:
            if self.current_task:
                self.root.after(0, lambda t=self.current_task: self.set_task_completed(t))

            with open(self.task_log_file, "a") as f:
                f.write(f"\nFinished: {datetime.now().isoformat()}\n")

            self.root.after(0, lambda: self.status_text.set("Status: Idle"))
            self.root.after(0, lambda: self.start_btn.config(state="normal"))
            self.root.after(0, lambda: self.stop_btn.config(state="disabled"))

    def stop_test(self):
        if self.running_process:
            self.status_text.set("Status: Stopping")
            self.running_process.terminate()
            time.sleep(1)
            if self.running_process.poll() is None:
                self.running_process.kill()

            if self.current_task:
                self.set_task_completed(self.current_task)

            with open(self.task_log_file, "a") as f:
                f.write(f"\nStopped by user: {datetime.now().isoformat()}\n")

            self.status_text.set("Status: Stopped")

    # ------------------------------------------------------------------
    # TASK STATE / ETA
    # ------------------------------------------------------------------

    def set_task_running(self, task):
        self.current_task = task
        self.task_start_time = time.time()

        for name, chk in self.task_checkboxes:
            if name == task:
                chk.configure(style="RunningTask.TCheckbutton")

        with open(self.task_log_file, "a") as f:
            f.write(f"[START] {task} @ {datetime.now().isoformat()}\n")

    def set_task_completed(self, task):
        if not self.task_start_time:
            return

        duration = time.time() - self.task_start_time
        self.task_durations.append(duration)

        with open(self.task_log_file, "a") as f:
            f.write(f"[STOP ] {task} @ {datetime.now().isoformat()} (Duration {duration:.1f}s)\n")

        for name, chk in self.task_checkboxes:
            if name == task:
                chk.configure(style="CompletedTask.TCheckbutton")
                chk.state(["disabled"])

        self.completed_tasks.add(task)
        self.task_start_time = None
        self.update_progress()
        self.update_eta()

    def update_progress(self):
        pct = int((len(self.completed_tasks) / len(self.selected_tasks)) * 100)
        self.progress_var.set(pct)

    def update_eta(self):
        remaining = len(self.selected_tasks) - len(self.completed_tasks)
        if remaining <= 0 or not self.task_durations:
            self.eta_text.set("ETA: --")
            return

        avg = sum(self.task_durations) / len(self.task_durations)
        eta = int(avg * remaining)
        m, s = divmod(eta, 60)
        self.eta_text.set(f"ETA: {m}m {s}s")

    # ------------------------------------------------------------------
    # LOGGING
    # ------------------------------------------------------------------

    def log_message(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

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
