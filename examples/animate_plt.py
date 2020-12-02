from pytrigno import TrignoAccel
from pytrigno import TrignoEMG
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import time

#Reading one sensor accel data:
#t=TrignoAccel(channel_range=(0,2),samples_per_read=100) #limit channels to 3 (0,1,2 according to accel_x, accel_y, accel_z)
#t.start()
#data=t.read()
#t.stop()
#print(data.shape, data.sum())
#print(data)

#Reading two sensors accel data:
#limit channels to 5 (0,1,2 according to sensor 1 accel_x, accel_y, accel_z and) and (3,4,5 to sensor 2 ...)

sensors_number = 1
acc_channels = 3*sensors_number
emg_channels = sensors_number

accel=TrignoAccel(channel_range=(0,acc_channels-1),samples_per_read=100) #limit channels to 5
accel.start()

fig, axs = plt.subplots(3)

xs = []
acc_x = []
acc_y = []
acc_z = []

def animate(i, xs, acc_x, acc_y, acc_z):
    start_time = time.time()
    data = accel.read()

    acc_x.extend(data[0,:])
    acc_y.extend(data[1,:])
    acc_z.extend(data[2,:])
    acc_x = acc_x[-1000:]
    acc_y = acc_y[-1000:]
    acc_z = acc_z[-1000:]
    axs[0].clear()
    axs[1].clear()
    axs[2].clear()
    axs[0].plot(acc_x)
    axs[1].plot(acc_y)
    axs[2].plot(acc_z)
    print("--- %f seconds ---" % (time.time() - start_time))

ani = animation.FuncAnimation(fig, animate, fargs=(xs, acc_x, acc_y, acc_z), interval=100)
plt.show()
accel.stop()
