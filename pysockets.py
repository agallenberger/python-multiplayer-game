## =================================================================================================
## Python 3.6+
## =================================================================================================
import socket

## =================================================================================================
PORT        = 10002
STARTBYTE   = '\n'
ENCODING    = 'utf-8'

## =================================================================================================
def send_msg(socket, message):
    '''
    Sends message over TCP

    :param socket: Either connection or socket obj
    :param message: string
    :return: None
    '''
    ## Message is: STARTBYTE + 8 digit message length + message
    msg = f'{STARTBYTE}{len(message):08d}{message}'
    socket.sendall(msg.encode(ENCODING))


## -------------------------------------------------------------------------------------------------
def receive_msg(socket):
    '''
    Receives message over TCP

    :param socket: Either connection or socket obj
    :return: string
    '''
    startbyte = socket.recv(1).decode(ENCODING)
    while startbyte != STARTBYTE:
        startbyte = socket.recv(1).decode(ENCODING)

    return socket.recv(int(socket.recv(8).decode(ENCODING))).decode(ENCODING)


## -------------------------------------------------------------------------------------------------
def is_valid_address(addr):
    '''
    Check if a IP:PORT address is valid

    :param addr: string IP:PORT
    :return: True/False
    '''
    try:
        ip, port = addr.split(':')
        ip_split = ip.split('.')
    except ValueError:
        return False

    ## Check if port is integer within [0, 65535]
    try:
        if int(port) > 65535 or int(port) < 0:
            return False
    except ValueError:
        return False

    ## Check if IP contains 4 numbers
    if len(ip_split) != 4:
        return False

    ## Check if IP numbers are integers within [0, 255]
    for n in ip_split:
        try:
            if int(n) < 0 or int(n) > 255:
                return False
        except ValueError:
            return False

    ## This is a valid address
    return True


## -------------------------------------------------------------------------------------------------
def get_ip():
    '''
    Gets the internal IP address of the current device. OS independent.

    :return: IP
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception as e:
        print(f'{e}!r')
        ip = '127.0.0.1'
    finally:
        s.close()

    return ip

