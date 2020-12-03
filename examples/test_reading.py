from pytrigno import TrignoOrientation
import time
from scipy.spatial.transform import Rotation as R
import matplotlib.pyplot as plt
import matplotlib.animation as animation

import numpy as np
sensors_number = 1
acc_channels = 3*sensors_number
emg_channels = sensors_number
orientation_channels = 4*sensors_number #for quaternion
orientation = TrignoOrientation(channel_range=(0,orientation_channels-1),samples_per_read=170)

orientation.is_paired(1)
time.sleep(1)
orientation.is_active(1)
time.sleep(1)
orientation.what_mode(1)
time.sleep(1)
orientation.start()
time.sleep(3)

xs = []
ys = []
r = []
p = []
y = []
fig, axs = plt.subplots(3)

def animate(i, xs, r, p, y):
    start_time = time.time()
    data = orientation.read_all()
    print('R1', np.sum(data))
    print("R1--- %f seconds ---" % (time.time() - start_time))
    start_time_dwa = time.time()
    data = orientation.read()
    print('R2', np.sum(data))
    print("R2--- %f seconds ---" % (time.time() - start_time_dwa))

    if any([data[0,-1], data[1,-1], data[2,-1],data[3,-1]]):
        orientation_quat = R.from_quat([data[0,-1], data[1,-1], data[2,-1],data[3,-1]])
        #orientation_quats = R.from_quat(np.transpose([data[0, :], data[1, :], data[2, :], data[3, :]]))
        #iters=any([data[0, :], data[1, :], data[2, :], data[3, :]])
        orientation_rpy = orientation_quat.as_euler('zyx', degrees=True)
        r.append(orientation_rpy[0])
        p.append(orientation_rpy[1])
        y.append(orientation_rpy[2])
        print(np.shape(data))
        #acc_x.extend(data[0,:])
        #acc_y.extend(data[1,:])
        #acc_z.extend(data[2,:])
        r = r[-1000:]
        p = p[-1000:]
        y = y[-1000:]
        axs[0].clear()
        axs[1].clear()
        axs[2].clear()
        axs[0].plot(r)
        axs[1].plot(p)
        axs[2].plot(y)
    #print("--- %f seconds ---" % (time.time() - start_time))


ani = animation.FuncAnimation(fig, animate, fargs=(xs, r, p, y), interval= 1000)
plt.show()
orientation.stop()
