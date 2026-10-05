# Application Startup Time Analyzer

Operating Systems Mini Project #7

## Objective
Measure and compare the startup time of commonly used applications.

## Technology
- Python 3
- Tkinter
- Matplotlib
- subprocess
- time.perf_counter()

## Run
1. Install Python 3.
2. Open a terminal in this folder.
3. Run:
   pip install -r requirements.txt
4. Start:
   python app.py

## Note
The measurement records process-launch/startup detection time. Actual application startup time can vary depending on CPU load, disk activity, background services, and whether the application is already cached.

## Main features
- Application selection
- Repeated startup measurements
- Results table
- Fastest/slowest/average summaries
- Comparison chart
- CSV export
