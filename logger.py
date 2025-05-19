import csv
from datetime import datetime
import os

def log_latency_to_csv(processing_latency, ui_latency, total_latency, filename="latency_log.csv"):
    """
    Logs latency metrics to a CSV file.
    
    Parameters:
        processing_latency (float): Time in milliseconds for processing data.
        ui_latency (float): Time in milliseconds to update UI.
        total_latency (float): Total time from receiving data to UI update.
        filename (str): CSV file path.
    """

    file_exists = os.path.isfile(filename)
    
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Timestamp", "ProcessingLatency(ms)", "UILatency(ms)", "TotalLatency(ms)"])
        
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            round(processing_latency, 2),
            round(ui_latency, 2),
            round(total_latency, 2)
        ])
