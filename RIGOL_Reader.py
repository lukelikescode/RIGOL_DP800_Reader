# FUNCTION: Read data via USB interface of RIGOL DP800-series machines.
# AUTHOR: Luke Gockowski 
# UPDATED: 05/06/2025
# NOTES: 
# > PyVISA requires libusb to run. Read PyVISA documentation for further details. 
# > In "rm.open_resource" replace with your device's address, found under "Utility" button.
import pyvisa
import time
import pandas as pd
import os


# CONNECT:
rm = pyvisa.ResourceManager()
rigol = rm.open_resource('USB0::0x1AB1::0x0E11::DP8C203804054::INSTR') # replace with device-specific address
print("Connected to ", rigol.query("*IDN?").strip())
rigol.timeout = 2000  # timeout error

# READ: 
# I've only programmed for channel 1, feel free to add others.
def read_measurements():
    voltage = float(rigol.query('MEAS:VOLT? CH1'))
    current = float(rigol.query('MEAS:CURR? CH1'))
    power = float(rigol.query('MEAS:POWE? CH1'))
    return voltage, current, power

# PREP DATA:
from datetime import date
from datetime import datetime
today_str = date.today().isoformat().replace('-','')
start_time = time.time()

def unique_filename(todaysdate=today_str,base_name='_powerLog_', extension='.csv'):
    i = 1
    while True:
        filename = f"{todaysdate}{base_name}{i}{extension}"
        if not os.path.exists(filename):
            return filename
        i += 1

csv_file = unique_filename()
    

# LOG DATA:
try:
    pd.DataFrame(columns=['TimeStamp','Time (s)','Voltage (V)','Current (A)','Power (W)']).to_csv(csv_file,index=False)
    while True:
        v, c, p = read_measurements()
        if(p>(v*c)): p = v*c # Hedge against occassional erroneous watt readings
        elapsed = time.time() - start_time
        print(f"t: {elapsed:.1f} s | V: {v:.3f} V | I: {c:.3f} A | P: {p:.3f} W")
        row = pd.DataFrame([{
            'TimeStamp': datetime.fromtimestamp(time.time()).strftime('%H:%M:%S'),
            'Time (s)': round(elapsed,3),
            'Voltage (V)': v,
            'Current (A)': c,
            'Power (W)': p
        }])

        row.to_csv(csv_file, mode='a', header=False, index=False)

        time.sleep(1) # choose the interval (seconds) at which you want to log
except KeyboardInterrupt: # Type "Ctrl-C" or equivalent in Terminal.
    print("Stopping logging...")
finally:
    rigol.close()
