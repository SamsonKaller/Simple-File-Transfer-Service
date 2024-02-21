################################################################################
#   Filename:       server.py
#
#   Authors:        Alexandre Vallières #40157223
#                   Samson Kaller       #40136815
#
#   Description:    Server-side script for the COEN366 Project "Simple File
#                   Transfer Service". See the project handout for more
#                   information on supported commands, command format, etc.
#                   - Listens for connections on PORT specified in input arguments
#                   - Accepts a client connection
#                   - While client connected, respond to requests
#                   - Debug flag '-d' can be passed to script to enable verbose
#                     printing of messages sent/received
#
################################################################################
from socket import socket, gethostname, gethostbyname, AF_INET, SOCK_STREAM
import os, argparse

############################## FUNCTIONS ##############################

# server calls putResponse() to handle and create a response to a client's PUT command
# Arguments:
#  - byte1: first byte received from client, integer value
#  - clientSocket: client socket to receive data, socket class
# Return:
#  - response byte with resCode in top 3 bits, 0b000 if SUCCESS, 0b101 if FAIL
def putResponse(byte1, clientSocket):

    # store opCode for debug print, top 3 bits of byte1
    opCode = byte1 >> 5
    # get the Filename Length, bottom 5 bits of byte1
    fNameLen = byte1 & 0x1F
    # use Filename Length to read the next bytes from client for Filename, decode to string
    fName = clientSocket.recv(fNameLen).decode()
    # read next 4 bytes from client for File Size, convert the 4 bytes into 1 integer, using big-endian notation
    fSize = int.from_bytes(clientSocket.recv(4), 'big')
    # use File Size to receive the whole file from client in bytes
    fBytes = clientSocket.recv(fSize)

    # now try to store the file, overwrites any existing file with same name
    try:
        # open in WRITE and BINARY mode for any type of file
        with open(fName, 'wb') as f:
            # write uploaded data to file
            f.write(fBytes)
        # store response code for SUCCESS
        resCode = 0b000
        # no error msg when successful
        err = ''

    # catch exceptions during write
    except:
        ### The project documentation does not specify a response code for PUT failures,    ###
        ### but we assume there might be failures if there isnt enough free space to create ###
        ### the file, or another such error. Since the SUCCESS response code for PUT is the ###
        ### same as CHANGE, we made the UNSUCCESS response code for PUT the same as CHANGE, ###
        ### ie: 0b101: response for unsuccessful change/put

        # store response code for FAIL
        resCode = 0b101
        # error msg for put failure
        err = 'ERROR: Could not create file "' + fName + '"'

    # print request and the response data when debug enabled
    if DEBUG == 1:
        print('***** PUT REQUEST *****')
        print(f'  opCode:  0b{opCode:03b}-----')
        print(f'  FL:      0b---{fNameLen:05b}')
        print( '  fName:   ' + fName)
        print(f'  FS:      0x{fSize:08X}')
        print( '  Data:    ', end='')
        print(fBytes)
        print('***** PUT RESPONSE *****')
        print(f'  resCode: 0b{resCode:03b}')

    # always print atleast the command type and filename for PUT
    print('Client PUT request: ' + fName)
    # print err if not empty
    if err != '': print(err)
    
    # return the response (in bytes array)
    return (resCode << 5).to_bytes(1, 'big')

# server calls getResponse() to handle and create its response to a client's GET command
# Arguments:
#  - byte1: first byte received from client, integer value
#  - clientSocket: client socket to receive data, socket class
# Return:
#  - response, one byte with resCode 0b010 in top 3 bits for FAIL, multiple bytes with header and data for SUCCESS
def getResponse(byte1, clientSocket):

    # store opCode for debug print, top 3 bits of byte1
    opCode = byte1 >> 5
    # get the Filename Length, bottom 5 bits of byte1
    fNameLen = byte1 & 0x1F
    # use Filename Length to read the next bytes from client for Filename, decode to string
    fName = clientSocket.recv(fNameLen).decode()

    # now try to read the file, fails if file does not exist
    try:
        # open in READ and BINARY mode for any type of file
        with open(fName, 'rb') as f:
            # read and store data from file
            fBytes = f.read()
        # get the file size
        fSize = len(fBytes)
        # store response code for SUCCESS
        resCode = 0b001
        # build full request with resCode, FL, Filename, FS, and Data
        response = ((resCode << 5) + fNameLen).to_bytes(1, 'big') + fName.encode() + fSize.to_bytes(4, 'big') + fBytes
        # no error msg when successful
        err = ''
    
    # catch exceptions during read
    except:
        # store response code for FAIL (File Not found)
        resCode = 0b010
        # File not found response is only 1 byte
        response = (resCode << 5).to_bytes(1, 'big')
        # error msg for GET failure
        err = 'ERROR: File not found'

    # print request and the response data when debug enabled
    if DEBUG == 1:
        print('***** GET REQUEST *****')
        print(f'  opCode:  0b{opCode:03b}-----')
        print(f'  FL:      0b---{fNameLen:05b}')
        print( '  fName:   ' + fName)
        print('***** GET RESPONSE *****')
        print(f'  resCode: 0b{resCode:03b}-----')

        # only print relevant data for SUCCESSFUL get resCode '0b001'
        if resCode == 0b001:
            print(f'  FL:      0b---{fNameLen:05b}')
            print( '  fName:   ' + fName)
            print(f'  FS:      0x{fSize:08X}')
            print( '  Data:    ', end='')
            print(fBytes)

    # always print atleast the command type and filename for GET
    print('Client GET request: ' + fName)
    # print err if not empty
    if err != '': print(err)

    # return the response (in bytes array)
    return response

# server calls changeResponse() to handle and create a response to a client's CHANGE command
# Arguments:
#  - byte1: first byte received from client, integer value
#  - clientSocket: client socket to receive data, socket class
# Return:
#  - response byte with resCode in top 3 bits, 0b000 if SUCCESS, 0b101 if FAIL
def changeResponse(byte1, clientSocket):
    
    # store opCode for debug print, top 3 bits of byte1
    opCode = byte1 >> 5
    # get the old Filename Length, bottom 5 bits of byte1
    oldNameLen = byte1 & 0x1F
    # use old Filename Length to read the next bytes from client for old Filename, decode to string
    oldName = clientSocket.recv(oldNameLen).decode()
    # read next byte from client for new Filename Length, and convert the byte into integer using big-endian notation
    newNameLen = int.from_bytes(clientSocket.recv(1), 'big')
    # use new Filename Length to read the next bytes from client for new Filename, decode to string
    newName = clientSocket.recv(newNameLen).decode()

    # now try to rename file, fails if file does not exist
    try:
        # rename the file
        os.rename(oldName, newName)
        # store response code for SUCCESS
        resCode = 0b000
        # no error msg when successful
        err = ''

    # catch exceptions during rename
    except:
        # store response code for FAIL (Unsuccessful change)
        resCode = 0b101
        # error msg for CHANGE failure
        err = 'ERROR: Change unsuccessful.'

    # print request and the response data when debug enabled
    if DEBUG == 1:
        print('***** CHANGE REQUEST *****')
        print(f'  opCode:  0b{opCode:03b}-----')
        print(f'  OFL:     0b---{oldNameLen:05b}')
        print( '  oldName: ' + oldName)
        print(f'  NFL:     0b---{newNameLen:05b}')
        print( '  newName: ' + newName)
        print('***** CHANGE RESPONSE *****')
        print(f'  resCode: 0b{resCode:03b}')

    # always print atleast the command type and filenames for CHANGE
    print('Client CHANGE request: ' + oldName + ' to ' + newName)
    # print err if not empty
    if err != '': print(err)

    # return the response (in bytes array)
    return (resCode << 5).to_bytes(1, 'big')

# server calls helpResponse() to handle and create a response to a client's HELP command
# Arguments:
#  - byte1: first byte received from client, integer value
#  - HELP_DATA: commands supported by server, string
# Return:
#  - response byte with resCode in top 3 bits, 0b000 if SUCCESS, 0b101 if FAIL
def helpResponse(byte1, HELP_DATA):

    # store opCode for debug print, top 3 bits of byte1
    opCode = byte1 >> 5
    # store resCode for debug print
    resCode = 0b110
    # encode given HELP string into bytes
    helpData = HELP_DATA.encode()
    # get the length of HELP msg
    length = len(helpData)

    # print request and the response data when debug enabled
    if DEBUG == 1:
        print('***** HELP REQUEST *****')
        print(f'  opCode:  0b{opCode:03b}-----')
        print('***** HELP RESPONSE *****')
        print(f'  resCode: 0b{resCode:03b}-----')
        print(f'  length:  0b---{length:05b}')
        print( '  Data:   ', end='')
        print(helpData)

    # always print atleast the command type for HELP
    print('Client HELP request')

    # return the response (in bytes array), byte1 + data
    return ((resCode << 5) + length).to_bytes(1, 'big') + helpData

############################## MAIN CODE ##############################

# if this script was called directly, and not as module by another script
if __name__ == '__main__':

    # accept arguments when calling script
    parser = argparse.ArgumentParser(description='Backend for FTP socket server', epilog='Requires Python 3.10 or higher to run')
    parser.add_argument('port', type=int, help='Port number on which the server is listening')
    parser.add_argument('-d', '--debug', action='store_const', const=1, default=0, help='Debug: print everything sent/received by server')
    sysArgs = parser.parse_args()

    # define input, constants
    SERVER_PORT = sysArgs.port
    DEBUG = sysArgs.debug
    HELP_DATA = 'get, put, change, help, bye'

    # create server TCP socket
    serverSocket = socket(AF_INET, SOCK_STREAM)
    # bind socket to IP and PORT, blank IP means use this computer's address
    serverSocket.bind(('', SERVER_PORT))
    serverSocket.listen(1) # start listening, max 1 connection at a time
    print(f'Server listening on {gethostbyname(gethostname())}:{SERVER_PORT}')

    # loop forever listening for clients
    while True:
    
        # block and wait for client connection to accept
        clientSocket, addr = serverSocket.accept()
        # print IP address of new connection
        print('New connection: ' + addr[0])
 
        # loop until client send 'bye' command
        while True:
            # READ FIRST BYTE SENT BY CLIENT ONLY, contains the opCode which decides how
            # the server reacts to the rest of data inbound on socket
            # convert the byte to integer as well
            byte1 = int.from_bytes(clientSocket.recv(1), 'big')

            # use top 3 bits of byte1, opCode, to determine how server handles request and formulates response
            match byte1 >> 5:

                # opCode 0b000 means PUT request, create PUT response
                case 0b000: response = putResponse(byte1, clientSocket)

                # opCode 0b001 means GET request, create GET response
                case 0b001: response = getResponse(byte1, clientSocket)
                
                # opCode 0b010 means CHANGE request, create CHANGE response
                case 0b010: response = changeResponse(byte1, clientSocket)

                # opCode 0b011 means HELP request, create HELP response
                case 0b011: response = helpResponse(byte1, HELP_DATA)
                
                # opCode 0b100 means BYE request, break while loop
                case 0b100: break

                # default is that server did not recognize the opCode, send 0b011 "ERROR-Unknown Request" response
                case _: response = (0b011 << 5).to_bytes(1, 'big')

            # send the response created above
            clientSocket.send(response)

        # close connection to client and print IP address of closed client connection
        clientSocket.close()
        print('Closed Connection: ' + addr[0])

    # close server socket :
    ### the server is always listening to accept new connections and doesnt
    ### accept user input for quitting, so the code execution never reaches this point.
    ### Therefore the following two lines are unnecessary and have been commented out.
    #server.close()
    #print('server exit')
