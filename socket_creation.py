import pyvisa


def create_socket(name_or_ip, socket = False, port = 0):
    """
    this function attempts to establish a pyvisa connection to device with given name or IP. Connection can be
    established via LAN or USB.

    name_or_ip requires the user to input the name of the device or it's IP. If the name of the device is not known,
    IP needs to be used. Only input the name of the device, without its manufacturer (example: "RIGOL DS1104" is
    incorrect, instead only "DS1104Z" should be written.)

    socket specifies if
    """

    # assert if given options match available options
    assert socket in [True, False]

    # Check if name_or_ip is name or ip
    is_name = False
    if any(i.isalpha() for i in name_or_ip):
        # if string has letters, assume given parameter is name
        is_name = True

    """
    if the given parameter is IP, enter this branch. In this branch a direct connection with the given ip will be 
    attempted. when the connection is established an identification request (*IDN?) will be sent to the device.
    If the device responds, the connection is maintained and a confirmation of successful connection is given.
    If the device does not respond, an error is raised, notifying of failed socket creation and connection is closed.
    """
    if is_name is False:

        # create resource manager for pyvisa
        rm = pyvisa.ResourceManager("@py")  # @py specifies the backend of pyvisa. in this case it is set to pyvisa_py

        if socket is False:
            # if IP is given, try connecting to said IP

            # create connection using given ip
            print("\n---------------------------------------------------")
            print("Attempting to establish connection to ip {0}...".format(name_or_ip))
            addr = rm.open_resource("TCPIP::{0}::INSTR".format(name_or_ip))
            addr.read_termination = '\n'  # specifies what end character signals termination; prevents timeouts
            addr.write_termination = '\n'  # specifies what end character signals termination; prevents timeouts

            # test if device on given ip is valid and correct
            try:
                device_id = addr.query("*IDN?")

            # if the device does not answer, raise error and close connection
            except Exception:
                addr.close()
                raise ValueError("ERROR: device with IP {0} did not respond! Please check if given IP and port are"
                                 "correct and try again.")

            if device_id:
                print("Device {0} successfully connected to socket TCPIP::{1}::INSTR.".format(device_id, name_or_ip))

        if socket is True:
            # if socket is set to true, attempt to make connection using the socket function instead of INSTR
            print("\n---------------------------------------------------")
            print("Attempting to establish connection to ip {0}...".format(name_or_ip))
            try:
                addr = rm.open_resource("TCPIP0::{0}::{1}::SOCKET".format(name_or_ip, port))
            except Exception:
                raise ValueError("ERROR: device on socket {0}:{1} did not respond!".format(name_or_ip, port))
            addr.read_termination = '\n'  # specifies what end character signals termination; prevents timeouts
            addr.write_termination = '\n'  # specifies what end character signals termination; prevents timeouts

            # send identification command to given IP
            try:
                device_id = addr.query("*IDN?")

            # if the device does not answer, raise error and close connection
            except Exception:
                addr.close()
                raise ValueError("ERROR: device with IP {0} did not respond! Please check if given IP and port are"
                                 "correct and try again.")

            # else if device responds, return message of success
            if device_id:
                print("Device {0} successfully connected to socket TCPIP::{1}::INSTR.".format(device_id, name_or_ip))
                print("---------------------------------------------------")


    elif is_name:

        if socket:
            raise ValueError("ERROR: Socket is enabled, meaning only IP is accepted but name was given! Enter a"
                             "valid IP address or disable socket setting.")

        # create resource manager for pyvisa
        rm = pyvisa.ResourceManager("@py")  # @py specifies the backend of pyvisa. in this case it is set to pyvisa_py

        # create resource list
        resource_list = rm.list_resources()
        print(resource_list)

        # if resource list is empty, raise error
        if resource_list == ():
            raise ValueError("ERROR: Resource list empty, no active devices found! Please make sure the device is"
                             "properly connected and try again. If error persists, try connecting the device via "
                             "different connection (LAN, USB).")

        # loop that goes through all the resources in resource list and asks each device for their id/ name.
        # socket is open for each device before *IDN? is sent. If device does not match given name, the socket is closed
        iteration = 0
        print("\n---------------------------------------------------")
        print("Attempting to find device with given name ({0})...".format(name_or_ip))

        for resource in resource_list:
            device_id = "not defined"
            iteration = iteration + 1

            # open socket for each address in resource list
            if resource.find('ASRL'):
                addr = rm.open_resource("{0}".format(resource))
                addr.read_termination = '\n'  # specifies what end character signals termination; prevents timeouts
                addr.write_termination = '\n'  # specifies what end character signals termination; prevents timeouts
                try:
                    # ask device for it's ID
                    device_id = addr.query("*IDN?")
                    print("Attempting to connect to {0}...".format(resource))
                except Exception:
                    # if there is no reply, pass
                    print("{0} did not reply... ".format(resource))
                    pass

            # if returned idn includes correct device id, keep socket open and exit for loop
            if name_or_ip in device_id:
                print("Device {0} successfully connected to socket {1}".format(name_or_ip, resource))
                print("---------------------------------------------------")
                break

            # if it doesn't, notify user what device is on current IP
            else:
                print("Device on socket {0} is {1}, not {2}.".format(resource, device_id, name_or_ip))
                try:
                    addr.close()
                except Exception:
                    pass

            # if for loop ends and device hasn't been found yet, return error message
            if iteration == len(resource_list):
                print("Device {0} could not be found.".format(name_or_ip))
                print("---------------------------------------------------")

    else:
        raise ValueError("ERROR: Given parameter is not ip or name! Please insert correct ip or name of device.")

    return addr
