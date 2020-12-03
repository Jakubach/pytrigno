import socket
import struct
import numpy

class _BaseTrignoDaq(object):
    """
    Delsys Trigno wireless EMG system.

    Requires the Trigno Control Utility to be running.

    Parameters
    ----------
    host : str
        IP address the TCU server is running on.
    cmd_port : int
        Port of TCU command messages.
    data_port : int
        Port of TCU data access.
    rate : int
        Sampling rate of the data source.
    total_channels : int
        Total number of channels supported by the device.
    timeout : float
        Number of seconds before socket returns a timeout exception

    Attributes
    ----------
    BYTES_PER_CHANNEL : int
        Number of bytes per sample per channel. EMG and accelerometer data
    CMD_TERM : str
        Command string termination.

    Notes
    -----
    Implementation details can be found in the Delsys SDK reference:
    http://www.delsys.com/integration/sdk/
    """

    BYTES_PER_CHANNEL = 4
    CMD_TERM = '\r\n\r\n'
    #CONFIGURATION_MODES = {'EMG':40, 'EMGACC':3, 'EMGGYRO':7, 'EMGIMU':65, 'EMGORIENTATION':66, 'IMU':609}
    CONFIGURATION_MODES = {'40':'EMG', '3':'EMG+ACC', '7':'EMG+GYRO', '65':'EMG+IMU', '66':'EMG+ORIENTATION', '609':'IMU'}

    def __init__(self, host, cmd_port, data_port, total_channels, timeout):
        self.host = host
        self.cmd_port = cmd_port
        self.data_port = data_port
        self.total_channels = total_channels
        self.timeout = timeout

        self._min_recv_size = self.total_channels * self.BYTES_PER_CHANNEL

        self._initialize()

    def _initialize(self):

        # create command socket and consume the servers initial response
        self._comm_socket = socket.create_connection(
            (self.host, self.cmd_port), self.timeout)
        self._comm_socket.recv(1024)

        # create the data socket
        self._data_socket = socket.create_connection(
            (self.host, self.data_port), self.timeout)

    def start(self):
        """
        Tell the device to begin streaming data.

        You should call ``read()`` soon after this, though the device typically
        takes about two seconds to send back the first batch of data.
        """
        self._send_cmd('START')

    def read_all(self, timeout = 20): #timeout in ms
        #https: // stackoverflow.com / questions / 2719017 / how - to - set - timeout - on - pythons - socket - recv - method
        self._data_socket.setblocking(False)
        packet = bytes()
        lacking_bytes = 0
        while(True):
            try:
                packet += self._data_socket.recv(lacking_bytes + self._min_recv_size)
            except BlockingIOError: #add timeout exception
                lacking_bytes = len(packet) % self._min_recv_size
                if(lacking_bytes == 0):
                    break
                else:
                    pass
        number_of_samples = int(len(packet) / self._min_recv_size)
        print(number_of_samples)
        data = numpy.asarray(
            struct.unpack('<' + 'f' * self.total_channels * number_of_samples, packet))
        data = numpy.transpose(data.reshape((-1, self.total_channels)))
        self._data_socket.setblocking(True)
        return data

    def read(self, num_samples):
        """
        Request a sample of data from the device.

        This is a blocking method, meaning it returns only once the requested
        number of samples are available.

        Parameters
        ----------
        num_samples : int
            Number of samples to read per channel.

        Returns
        -------
        data : ndarray, shape=(total_channels, num_samples)
            Data read from the device. Each channel is a row and each column
            is a point in time.
        """
        l_des = num_samples * self._min_recv_size
        l = 0
        packet = bytes()
        while l < l_des:
            try:
                packet += self._data_socket.recv(l_des - l)
            except socket.timeout:
                l = len(packet)
                packet += b'\x00' * (l_des - l)
                raise IOError("Device disconnected.")
            l = len(packet)

        data = numpy.asarray(
            struct.unpack('<'+'f'*self.total_channels*num_samples, packet))
        data = numpy.transpose(data.reshape((-1, self.total_channels)))

        return data

    def stop(self):
        """Tell the device to stop streaming data."""
        self._send_cmd('STOP')

    def reset(self):
        """Restart the connection to the Trigno Control Utility server."""
        self._initialize()

    def __del__(self):
        try:
            self._comm_socket.close()
        except:
            pass

    def _send_cmd(self, command, return_reply = False):
        self._comm_socket.send(self._cmd(command))
        raw_resp = self._comm_socket.recv(128)
        formated_resp = self._get_reply(raw_resp)
        if('?') in command:
            print("Query: {} <->  Reply: {}".format(command, formated_resp))
        else:
            print("Command: {} <->  Reply: {}".format(command, formated_resp))
        if return_reply:
            return formated_resp

    def _get_reply(self, response):
        reply = struct.unpack(str(len(response)) + 's', response)
        reply = reply[0].decode(encoding='ascii')
        if(self.CMD_TERM in reply):
            reply = reply.replace(self.CMD_TERM,'')
        return reply

    def set_mode(self,sensor_number, mode_number):
        self._send_cmd(f'SENSOR {sensor_number} SETMODE {mode_number}')

    def pair_sensor(self,sensor_number):
        self._send_cmd(f'SENSOR {sensor_number} PAIR')

    def is_paired(self, sensor_number):
        self._send_cmd(f'SENSOR {sensor_number} PAIRED?')

    def what_mode(self,sensor_number):
        reply = self._send_cmd(f'SENSOR {sensor_number} MODE?', return_reply = True)
        try:
            print(f'This is {self.CONFIGURATION_MODES[reply]} mode.')
        except:
            print('Unrecognized mode')

    def is_active(self,sensor_number):
        '''
        TODO: List active sensors

        :param sensor_number:
        :return:
        '''
        self._send_cmd(f'SENSOR {sensor_number} ACTIVE?')

    @staticmethod
    def _cmd(command):
        return bytes("{}{}".format(command, _BaseTrignoDaq.CMD_TERM),
                     encoding='ascii')

    @staticmethod
    def _validate(response):
        s = str(response)
        if 'OK' not in s:
            print("warning: TrignoDaq command failed: {}".format(s))


class TrignoEMG(_BaseTrignoDaq):
    """
    Delsys Trigno wireless EMG system EMG data.

    Requires the Trigno Control Utility to be running.

    Parameters
    ----------
    channel_range : tuple with 2 ints
        Sensor channels to use, e.g. (lowchan, highchan) obtains data from
        channels lowchan through highchan. Each sensor has a single EMG
        channel.
    samples_per_read : int
        Number of samples per channel to read in each read operation.
    units : {'V', 'mV', 'normalized'}, optional
        Units in which to return data. If 'V', the data is returned in its
        un-scaled form (volts). If 'mV', the data is scaled to millivolt level.
        If 'normalized', the data is scaled by its maximum level so that its
        range is [-1, 1].
    host : str, optional
        IP address the TCU server is running on. By default, the device is
        assumed to be attached to the local machine.
    cmd_port : int, optional
        Port of TCU command messages.
    data_port : int, optional
        Port of TCU EMG data access. By default, 50041 is used, but it is
        configurable through the TCU graphical user interface.
    timeout : float, optional
        Number of seconds before socket returns a timeout exception.

    Attributes
    ----------
    rate : int
        Sampling rate in Hz.
    scaler : float
        Multiplicative scaling factor to convert the signals to the desired
        units.
    """

    def __init__(self, channel_range, samples_per_read, units='V',
                 host='localhost', cmd_port=50040, data_port=50041, timeout=10):
        super(TrignoEMG, self).__init__(
            host=host, cmd_port=cmd_port, data_port=data_port,
            total_channels=16, timeout=timeout)

        self.channel_range = channel_range
        self.samples_per_read = samples_per_read

        self.rate = 2000

        self.scaler = 1.
        if units == 'mV':
            self.scaler = 1000.
        elif units == 'normalized':
            # max range of EMG data is 11 mV
            self.scaler = 1 / 0.011

    def set_channel_range(self, channel_range):
        """
        Sets the number of channels to read from the device.

        Parameters
        ----------
        channel_range : tuple
            Sensor channels to use (lowchan, highchan).
        """
        self.channel_range = channel_range
        self.num_channels = channel_range[1] - channel_range[0] + 1

    def read(self):
        """
        Request a sample of data from the device.

        This is a blocking method, meaning it returns only once the requested
        number of samples are available.

        Returns
        -------
        data : ndarray, shape=(num_channels, num_samples)
            Data read from the device. Each channel is a row and each column
            is a point in time.
        """
        data = super(TrignoEMG, self).read(self.samples_per_read)
        data = data[self.channel_range[0]:self.channel_range[1]+1, :]
        return self.scaler * data


class TrignoAccel(_BaseTrignoDaq):
    """
    Delsys Trigno wireless EMG system accelerometer data.

    Requires the Trigno Control Utility to be running.

    Parameters
    ----------
    channel_range : tuple with 2 ints
        Sensor channels to use, e.g. (lowchan, highchan) obtains data from
        channels lowchan through highchan. Each sensor has three accelerometer
        channels.
    samples_per_read : int
        Number of samples per channel to read in each read operation.
    host : str, optional
        IP address the TCU server is running on. By default, the device is
        assumed to be attached to the local machine.
    cmd_port : int, optional
        Port of TCU command messages.
    data_port : int, optional
        Port of TCU accelerometer data access. By default, 50042 is used, but
        it is configurable through the TCU graphical user interface.
    timeout : float, optional
        Number of seconds before socket returns a timeout exception.
    """
    def __init__(self, channel_range, samples_per_read, host='localhost',
                 cmd_port=50040, data_port=50042, timeout=10):
        super(TrignoAccel, self).__init__(
            host=host, cmd_port=cmd_port, data_port=data_port,
            total_channels=48, timeout=timeout)

        self.channel_range = channel_range
        self.samples_per_read = samples_per_read

        self.rate = 148.1

    def set_channel_range(self, channel_range):
        """
        Sets the number of channels to read from the device.

        Parameters
        ----------
        channel_range : tuple
            Sensor channels to use (lowchan, highchan).
        """
        self.channel_range = channel_range
        self.num_channels = channel_range[1] - channel_range[0] + 1

    def read(self):
        """
        Request a sample of data from the device.

        This is a blocking method, meaning it returns only once the requested
        number of samples are available.

        Returns
        -------
        data : ndarray, shape=(num_channels, num_samples)
            Data read from the device. Each channel is a row and each column
            is a point in time.
        """
        data = super(TrignoAccel, self).read(self.samples_per_read)
        data = data[self.channel_range[0]:self.channel_range[1]+1, :]
        return data

class TrignoOrientation(_BaseTrignoDaq):
    """
    Delsys Trigno wireless EMG system orientation data.

    Requires the Trigno Control Utility to be running.

    Parameters
    ----------
    channel_range : tuple with 2 ints
        Sensor channels to use, e.g. (lowchan, highchan) obtains data from
        channels lowchan through highchan. Each sensor has three accelerometer
        channels.
    samples_per_read : int
        Number of samples per channel to read in each read operation.
    host : str, optional
        IP address the TCU server is running on. By default, the device is
        assumed to be attached to the local machine.
    cmd_port : int, optional
        Port of TCU command messages.
    data_port : int, optional
        Port of TCU accelerometer data access. By default, 50042 is used, but
        it is configurable through the TCU graphical user interface.
    timeout : float, optional
        Number of seconds before socket returns a timeout exception.
    """
    def __init__(self, channel_range, samples_per_read, host='localhost',
                 cmd_port=50040, data_port=50044, timeout=10):
        super(TrignoOrientation, self).__init__(
            host=host, cmd_port=cmd_port, data_port=data_port,
            total_channels=144, timeout=timeout)

        self.channel_range = channel_range
        self.samples_per_read = samples_per_read

        self.rate = 74

    def set_channel_range(self, channel_range):
        """
        Sets the number of channels to read from the device.

        Parameters
        ----------
        channel_range : tuple
            Sensor channels to use (lowchan, highchan).
        """
        self.channel_range = channel_range
        self.num_channels = channel_range[1] - channel_range[0] + 1

    def read(self):
        """
        Request a sample of data from the device.

        This is a blocking method, meaning it returns only once the requested
        number of samples are available.

        Returns
        -------
        data : ndarray, shape=(num_channels, num_samples)
            Data read from the device. Each channel is a row and each column
            is a point in time.
        """
        data = super(TrignoOrientation, self).read(self.samples_per_read)
        data = data[self.channel_range[0]:self.channel_range[1]+1, :]
        return data
