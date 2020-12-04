from pytrigno import TrignoAdapter

'''
trigno_sensors = TrignoAdapter()
hand_sensors = TrignoAdapter('hand')
#create sensor 1, 2
leg_sensors = TrignoAdapter('leg')
#create sensor 3, 4 #TODO check if used
arm_sensors = TrignoAdapter('Arm')
#create sensor 5, 6
arm_hand = TrignoAdapter(arm_sensors, hand_sensors)



trigno_sensors = TrignoAdapter('Kuba')
trigno_sensors.add('EMG', 'hand')
trigno_sensors.add('IMU', 'hand')
TrignoAdapter('hand')



#TrignoAdapter().
#trignoEMG = trigno_sensors.('EMG', 'label')
'''
trigno_sensors = TrignoAdapter()
trigno_sensors.add_sensor('EMG')
