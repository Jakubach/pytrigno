from pytrigno import TrignoOrientation
import time
sensors_number = 1
acc_channels = 3*sensors_number
emg_channels = sensors_number
orientation_channels = 4*sensors_number #for quaternion
orientation = TrignoOrientation(channel_range=(0,orientation_channels-1),samples_per_read=100)

orientation.is_paired(1)
time.sleep(1)
orientation.is_active(1)
time.sleep(1)
orientation.what_mode(1)
time.sleep(1)
