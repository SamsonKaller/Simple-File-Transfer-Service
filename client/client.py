################################################################################
#   Filename:       client.py
#
#   Authors:        Alexandre Vallières #40157223
#                   Samson Kaller       #40136815
#
#   Description:    Client-side script for the COEN366 Project "Simple File
#                   Transfer Service". See the project handout for more
#                   information on supported commands, command format, etc.
#                   - Connects to server (IP:PORT) specified in input arguments
#                   - accepts inputs from user
#                   - sends requests to server
#                   - handle reply from server
#                   - Debug flag '-d' can be passed to script to enable verbose
#                     printing of messages sent/received
#
################################################################################
from socket import socket, AF_INET, SOCK_STREAM
import argparse

############################## FUNCTIONS ##############################

# check for errors in input arguments for put/get/change commands
# Arguments:
#  - args: list of arguments (strings), command name is index=0
# Return:
#  - True if there is an incorrect number of arguments or filenames are too long
#  - False if there is no errors and the arguments can be used for a request
def inputErrors(args):
    # for all commands, need to check correct number of arguments,
    # then check if filenames for put/get/change are no longer than 30 chars,
    # leaving 1 char for end-of-string character: '\0'
    # * NOTE: python does not actually use the NULL byte to terminate strings *

    if args[0] == 'bye' or args[0] == 'help':
        # check for bad number of arguments to command (doesn't take any)
        if len(args) != 1:
            print("ERROR: Command takes no arguments, ex: '" + args[0] + "'")
            return True
 
    elif args[0] == 'put' or args[0] == 'get':
        # check for bad number of arguments to command
        if len(args) != 2:
            print("ERROR: Command takes 1 arguments, ex: '" + args[0] + " example.txt'")
            return True
        # check for filename too long error
        if len(args[1]) > 30:
            print('ERROR: Command filename must not exceed 30 characters.')
            return True

    elif args[0] == 'change':
        # check for bad number of arguments to command
        if len(args) != 3:
            print("ERROR: Command takes 2 arguments, ex: 'change oldName.txt newName.txt'")
            return True
        # check for either new or old filename too long error
        elif len(args[1]) > 30 or len(args[2]) > 30:
            print('ERROR: Command filenames must not exceed 30 characters.')
            return True

    return False    # no errors found, return false

# client calls putRequest() to create a PUT request to send file to server, does not send yet
# Arguments:
#  - fName: filename for PUT request, string
# Return:
#  - '': empty response if there was an error finding/reading the file
#  - put request: byte1 = opCode & FL, then file name, then FS (4 bytes), then file data
def putRequest(fName):

    # store opCode for PUT
    opCode = 0b000
    # get filename length
    fNameLen = len(fName)

    # try to open and read file
    try:
        # open the file
        with open(fName, 'rb') as f:
            # read all data from file
            fData = f.read()

        # get file size of data read
        fSize = len(fData)
        # error msg if fileSize is too great to fit in 4 bytes, else empty error ''
        err = f'ERROR: File too big, size = 0x{fSize:x}' if fSize > 0xFFFFFFFF else ''

    # error reading file
    except:
        err = 'ERROR: Could not read file "' + fName + '"'    

    # print request data when debug enabled
    if DEBUG == 1:
        print('***** PUT REQUEST *****')
        print(f'  opCode:  0b{opCode:03b}-----')
        print(f'  FL:      0b---{fNameLen:05b}')
        print( '  fName:   ' + fName)

        # print file size and data if no error
        if err == '':
            print(f'  FS:      0x{fSize:08X}')
            print( '  Data:    ', end='')
            print(fData)
        
    # if error, print it and return empty string
    if err != '': 
        print(err)
        return ''

    # build full request to send and return it
    return ((opCode << 5) + fNameLen).to_bytes(1, 'big') + fName.encode() + fSize.to_bytes(4, 'big') + fData

# client calls getRequest() to create a GET request to get file from server, does not send yet
# Arguments:
#  - fName: filename for GET request, string
# Return:
#  - get request: byte1 = opCode & FL, then Filename
def getRequest(fName):

    # store opCode for GET
    opCode = 0b001
    # get filename length
    fNameLen = len(fName)

    # print request data when debug enabled
    if DEBUG == 1:
        print('***** GET REQUEST *****')
        print(f'  opCode:  0b{opCode:03b}-----')
        print(f'  FL:      0b---{fNameLen:05b}')
        print( '  fName:   ' + fName)

    # build full request to send and return it
    return ((opCode << 5) + fNameLen).to_bytes(1, 'big') + fName.encode()

# client calls changeRequest() to create a CHANGE request to change filename on server, does not send yet
# Arguments:
#  - oldName: old filename for CHANGE request, string
#  - newName: new filename for CHANGE request, string
# Return:
#  - change request: byte1 = opCode & OFL, then old name, then NFL (1 byte), then new name
def changeRequest(oldName, newName):

    # store opCode for GET
    opCode = 0b010
    # get old filename length
    oldNameLen = len(oldName)
    # get new filename length
    newNameLen = len(newName)

    # print request data when debug enabled
    if DEBUG == 1:
        print('***** CHANGE REQUEST *****')
        print(f'  opCode:  0b{opCode:03b}-----')
        print(f'  OFL:     0b---{oldNameLen:05b}')
        print( '  oldName: ' + oldName)
        print(f'  NFL:     0b---{newNameLen:05b}')
        print( '  newName: ' + newName)

    # build full request to send and return it
    return ((opCode << 5) + oldNameLen).to_bytes(1, 'big') + oldName.encode() + newNameLen.to_bytes(1, 'big') + newName.encode()

# client calls getResponse() to handle a GET response from server, stores file
# Arguments:
#  - byte1: first byte received from server, integer value
#  - clientSocket: client socket to receive data, socket class
def getResponse(byte1, clientSocket):

    # store response code
    resCode = byte1 >> 5
    # store Filename Length
    fNameLen = byte1 & 0x1F
    # use Filename Length to read the next bytes from client for Filename, decode to string
    fName = clientSocket.recv(fNameLen).decode()
    # read next 4 bytes from client for File Size, convert the 4 bytes into 1 integer, using big-endian notation
    fSize = int.from_bytes(clientSocket.recv(4), 'big')
    # use File Size to receive the whole file from client in bytes
    fData = clientSocket.recv(fSize)

    # now try to store the file, overwrites any existing file with same name
    try:
        # open in WRITE and BINARY mode for any type of file
        with open(fName, 'wb') as f:
            # write downloaded data to file
            f.write(fData)
        # no error msg when successful
        err = ''
    except:
        # error msg for write failure
        err = 'Error: Could not save download file "' + fName + '"'

    # print response data when debug enabled
    if DEBUG == 1:
        print('***** GET RESPONSE *****')
        print(f'  resCode: 0b{resCode:03b}-----')
        print(f'  FL:      0b---{fNameLen:05b}')
        print( '  fName:   ' + fName)
        print( '  Data:    ', end='')
        print(fData)

    # print err if not empty, and return
    if err != '':
        print(err)
        return

    # print filename and success msg
    print(fName + ' has been downloaded successfully.')
    return

# client calls helpResponse() to handle a HELP response from server, prints commands from server
# Arguments:
#  - byte1: first byte received from server, integer value
#  - clientSocket: client socket to receive data, socket class
def helpResponse(byte1, clientSocket):

    # store response code
    resCode = byte1 >> 5
    # store help data Length
    helpLen = byte1 & 0x1F
    # use help data Length to read the next bytes from client for help data, decode to string
    helpData = clientSocket.recv(helpLen).decode()

    # print response data when debug enabled
    if DEBUG == 1:
        print('***** HELP RESPONSE *****')
        print(f'  resCode: 0b{resCode:03b}-----')
        print(f'  Length:  0b---{helpLen:05b}')
        print( '  Data:    ' + helpData)

    # print the commands received and return
    print('Commands are: ' + helpData)
    return

############################## MAIN CODE ##############################

# if this script was called directly, and not as module by another script
if __name__ == '__main__':

    # input argument parser
    parser = argparse.ArgumentParser(description='Client for FTP socket server', epilog='Requires Python 3.10 or higher to run')
    parser.add_argument('host', type=str, help='IP address of the server')
    parser.add_argument('port', type=int, help='Port number on which the server is listening')
    parser.add_argument('-d', '--debug', action='store_const', const=1, default=0, help='Debug: print everything sent/received by client')
    sysArgs = parser.parse_args()

    # get input arguments
    SERVER_HOST = sysArgs.host
    SERVER_PORT = sysArgs.port
    DEBUG = sysArgs.debug

    # create client TCP socket and connect to server
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((SERVER_HOST, SERVER_PORT))
    print('Session has been established!')

    # loop until exit
    while True:
        command = input('>> ')   # get command and arguments from user
        args = command.split(' ')  # split input line by space char ' '

        request = '' # create empty request

        # do input validation here, keeps match cases cleaner
        # checks number of arguments, and if filenames > 31 chars
        if inputErrors(args):
            # restart loop from beginning
            continue

        # try to match command in args[0] and make request with error-free inputs
        match args[0]:

            # found bye command, send opcode 0b100
            ### NOT SPECIFIED, chose unused '0b100' code for 'bye' command ###
            case 'bye': request = (0b100 << 5).to_bytes(1, 'big')
        
            # found help command, send opcode 0b011
            case 'help': request = (0b011 << 5).to_bytes(1, 'big')
        
            # found put command, create request with the validated input arguments
            case 'put': request = putRequest(args[1])
    
            # found get command, create request with the validated input arguments
            case 'get': request = getRequest(args[1])
            
            # found change command, create request with the validated input arguments
            case 'change': request = changeRequest(args[1], args[2])

            # command not recognized
            case _: request = (0b111 << 5).to_bytes(1, 'big')

        # only PUT command may fail at this point, if the file cannot be read
        # continue loop from beginning
        if request == '': continue

        # send request
        clientSocket.send(request)

        if args[0] == 'bye':
            # close client socket and end script
            clientSocket.close()
            print('client exit')
            break

        # get 1-byte response from server, convert byte to integer
        byte1 = int.from_bytes(clientSocket.recv(1), 'big')

        # print if debug enabled
        if DEBUG:
            print('***** SERVER RESPONSE *****')
            print(f'  resCode: 0b{(byte1 >> 5):03b}')

        # get byte1 opcode in top 3 bits and match
        match byte1 >> 5:

            # successfull put and change commands server response
            case 0b000:
                # if this was put command, print the uploaded filename
                if args[0] == 'put': print(args[1] + ' has been uploaded successfully.')
                # if this was change command, print old name and new name
                elif args[0] == 'change': print(args[1] + ' has been renamed to ' + args[2] + ' successfully.')

            # get response from server, need to further receive data in getResponse()
            case 0b001: getResponse(byte1, clientSocket)

            # server GET error response, file not found
            case 0b010: print('SERVER ERROR: File not found...')

            # server unknown request ERROR
            case 0b011: print("SERVER ERROR: Unknown request... Try 'help' to see commands supported by server.")
    
            # server CHANGE/PUT error response, unsuccessfull change
            case 0b101: print('SERVER ERROR: Command was unsuccessful...')

            # help response from server, need to further receive help data in helpResponse()
            case 0b110: helpResponse(byte1, clientSocket)