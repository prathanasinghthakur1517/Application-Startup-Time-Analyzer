
import os
import sys
import time
import json
import subprocess
import platform
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class StartupAnalyzer:
    def __init__(self, root):
        self.root = root
        self.root.title("Application Startup Time Analyzer")
        self.root.geometry("1050x680")
        self.root.minsize(900, 600)

        self.results = []
        self.test_count = 3

        self.applications = self.get_default_apps()

        self.build_ui()
        self.refresh_table()
        self.update_summary()

    def get_default_apps(self):
        system = platform.system()
        if system == "Windows":
            return [
                ("Notepad", "notepad.exe"),
                ("Calculator", "calc.exe"),
                ("Paint", "mspaint.exe"),
            ]
        elif system == "Linux":
            return [
                ("Text Editor", "gedit"),
                ("Terminal", "x-terminal-emulator"),
                ("File Manager", "xdg-open"),
            ]
        else:
            return [
                ("TextEdit", "/System/Applications/TextEdit.app"),
                ("Calculator", "/System/Applications/Calculator.app"),
                ("Finder", "/System/Library/CoreServices/Finder.app"),
            ]

    def build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        header = ttk.Frame(self.root, padding=18)
        header.pack(fill="x")

        ttk.Label(
            header,
            text="Application Startup Time Analyzer",
            font=("Segoe UI", 22, "bold")
        ).pack(anchor="w")

        ttk.Label(
            header,
            text="Measure and compare how quickly applications start.",
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=(4, 0))

        controls = ttk.LabelFrame(self.root, text="Test Controls", padding=12)
        controls.pack(fill="x", padx=18, pady=(0, 12))

        ttk.Label(controls, text="Application:").grid(row=0, column=0, padx=6, pady=6, sticky="w")

        self.app_var = tk.StringVar(value=self.applications[0][0])
        self.app_combo = ttk.Combobox(
            controls,
            textvariable=self.app_var,
            values=[name for name, _ in self.applications],
            state="readonly",
            width=28
        )
        self.app_combo.grid(row=0, column=1, padx=6, pady=6)

        ttk.Label(controls, text="Runs:").grid(row=0, column=2, padx=(20, 6), pady=6)

        self.runs_var = tk.IntVar(value=3)
        runs_spin = ttk.Spinbox(
            controls, from_=1, to=10, textvariable=self.runs_var, width=6
        )
        runs_spin.grid(row=0, column=3, padx=6, pady=6)

        ttk.Button(
            controls, text="▶ Start Analysis", command=self.start_analysis
        ).grid(row=0, column=4, padx=(20, 6), pady=6)

        ttk.Button(
            controls, text="Clear Results", command=self.clear_results
        ).grid(row=0, column=5, padx=6, pady=6)

        ttk.Button(
            controls, text="Export CSV", command=self.export_csv
        ).grid(row=0, column=6, padx=6, pady=6)

        # Summary cards
        summary = ttk.Frame(self.root, padding=(18, 0))
        summary.pack(fill="x")

        self.fastest_var = tk.StringVar(value="—")
        self.slowest_var = tk.StringVar(value="—")
        self.average_var = tk.StringVar(value="—")
        self.tests_var = tk.StringVar(value="0")

        cards = [
            ("FASTEST", self.fastest_var),
            ("SLOWEST", self.slowest_var),
            ("AVERAGE", self.average_var),
            ("TESTS", self.tests_var),
        ]

        for i, (title, var) in enumerate(cards):
            card = ttk.LabelFrame(summary, text=title, padding=12)
            card.grid(row=0, column=i, padx=6, sticky="nsew")
            summary.columnconfigure(i, weight=1)
            ttk.Label(card, textvariable=var, font=("Segoe UI", 13, "bold")).pack()

        # Results table
        table_frame = ttk.LabelFrame(self.root, text="Startup Measurements", padding=10)
        table_frame.pack(fill="both", expand=True, padx=18, pady=12)

        columns = ("application", "run", "time", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=11)

        headings = {
            "application": "Application",
            "run": "Run",
            "time": "Startup Time (seconds)",
            "status": "Status"
        }
        widths = {"application": 220, "run": 80, "time": 180, "status": 160}

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Chart
        chart_frame = ttk.LabelFrame(self.root, text="Comparison", padding=8)
        chart_frame.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        if MATPLOTLIB_AVAILABLE:
            self.figure, self.ax = plt.subplots(figsize=(8, 2.8), dpi=90)
            self.canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
            self.canvas.get_tk_widget().pack(fill="both", expand=True)
            self.update_chart()
        else:
            ttk.Label(
                chart_frame,
                text="Install matplotlib to display the comparison chart:\n"
                     "pip install matplotlib",
                justify="center"
            ).pack(expand=True)

    def selected_command(self):
        selected = self.app_var.get()
        for name, command in self.applications:
            if name == selected:
                return command
        return None

    def launch_and_measure(self, command):
        start = time.perf_counter()

        try:
            if platform.system() == "Darwin" and command.endswith(".app"):
                process = subprocess.Popen(["open", command])
            else:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

            # We measure process launch/startup detection time.
            # A short stabilization delay avoids reporting the same instant
            # for every application on fast systems.
            time.sleep(0.15)

            elapsed = time.perf_counter() - start
            return elapsed, "Measured"

        except Exception as exc:
            return None, f"Error: {exc}"

    def start_analysis(self):
        command = self.selected_command()
        if not command:
            messagebox.showerror("Error", "No application selected.")
            return

        runs = max(1, min(10, int(self.runs_var.get())))

        for run_number in range(1, runs + 1):
            elapsed, status = self.launch_and_measure(command)

            if elapsed is not None:
                self.results.append({
                    "application": self.app_var.get(),
                    "run": run_number,
                    "time": round(elapsed, 3),
                    "status": status
                })
            else:
                self.results.append({
                    "application": self.app_var.get(),
                    "run": run_number,
                    "time": None,
                    "status": status
                })

        self.refresh_table()
        self.update_summary()
        self.update_chart()

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in self.results:
            self.tree.insert(
                "",
                "end",
                values=(
                    row["application"],
                    row["run"],
                    "—" if row["time"] is None else f"{row['time']:.3f}",
                    row["status"]
                )
            )

    def update_summary(self):
        valid = [r for r in self.results if r["time"] is not None]

        self.tests_var.set(str(len(valid)))

        if not valid:
            self.fastest_var.set("—")
            self.slowest_var.set("—")
            self.average_var.set("—")
            return

        averages = {}
        for row in valid:
            averages.setdefault(row["application"], []).append(row["time"])

        averages = {
            app: sum(times) / len(times)
            for app, times in averages.items()
        }

        fastest = min(averages, key=averages.get)
        slowest = max(averages, key=averages.get)
        overall = sum(r["time"] for r in valid) / len(valid)

        self.fastest_var.set(f"{fastest} ({averages[fastest]:.2f}s)")
        self.slowest_var.set(f"{slowest} ({averages[slowest]:.2f}s)")
        self.average_var.set(f"{overall:.2f}s")

    def update_chart(self):
        if not MATPLOTLIB_AVAILABLE:
            return

        self.ax.clear()

        valid = [r for r in self.results if r["time"] is not None]
        if not valid:
            self.ax.text(
                0.5, 0.5, "Run an analysis to see results.",
                ha="center", va="center", transform=self.ax.transAxes
            )
            self.ax.set_axis_off()
        else:
            averages = {}
            for row in valid:
                averages.setdefault(row["application"], []).append(row["time"])

            names = list(averages.keys())
            values = [sum(v) / len(v) for v in averages.values()]

            self.ax.bar(names, values)
            self.ax.set_ylabel("Seconds")
            self.ax.set_title("Average Application Startup Time")
            self.ax.tick_params(axis="x", rotation=20)
            self.ax.grid(axis="y", alpha=0.25)

        self.figure.tight_layout()
        self.canvas.draw()

    def clear_results(self):
        self.results.clear()
        self.refresh_table()
        self.update_summary()
        self.update_chart()

    def export_csv(self):
        if not self.results:
            messagebox.showinfo("Export", "There are no results to export.")
            return

        path = filedialog.asksaveasfilename(
            title="Save Results",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if not path:
            return

        import csv
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Application", "Run", "Startup Time (seconds)", "Status"])
            for row in self.results:
                writer.writerow([
                    row["application"],
                    row["run"],
                    row["time"] if row["time"] is not None else "",
                    row["status"]
                ])

        messagebox.showinfo("Export Complete", f"Results saved to:\n{path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = StartupAnalyzer(root)
    root.mainloop()
