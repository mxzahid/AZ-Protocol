#!/usr/bin/env python

#SENDER PART OF AZP -> Abdullah Zahid Protocol
#this builds a TCP like protocol on top of UDP

import socket
import sys
import os
import socket
import signal
import time
import datetime
import functs #functs.py in the package which has necessary functions like ones to make a packet

windowSize = 1 #tested on this window size

if __name__ == '__main__':
    # See if all the arguments are there if not then raise error
    try:
        fileToSend, logFile = sys.argv[1], sys.argv[5]
        receiverIP, receiverPort, ackPort = socket.gethostbyname(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    except IndexError as TypeError:
        exit('All arguments were not provided, please refer to the explanation to see correct usage')
    
    try:
        # Init UDP sockets for sending packets
        sendSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sendSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sendSocket.bind(("", ackPort))
        # Init socket for getting acknowledgements 
        ackSocket = socket.socket()
        ackSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        ackSocket.bind(("", ackPort))
        ackSocket.listen(1)
    except socket.error:
        exit('Error creating sockets')

    #init variables
    sequenceNumber, ackNumber, SentNum, retransmittedNum = 0,0,0,0  
    timeout = 1
    lastPacket, connectionEstablished= False, False
     #connectionEstablished will turn true after first packet makes it

    try:
        sendFile = open(fileToSend, 'rb')
    except:
        exit("Error opening file: " + fileToSend)

    try:
        logF = open(logFile, 'wb')
    except IOError:
        exit("Unable to open " + logFile)


    currText = sendFile.read(556)

    # keeps sending initial packet until connection is made
    while not connectionEstablished:
        try:
            packet = functs.makePacket(ackPort, receiverPort,sequenceNumber, ackNumber, False, False, windowSize, currText)
            sendSocket.sendto(packet, (receiverIP, receiverPort))
            SentNum += 1
            sendTime = time.time()

            signal.signal(signal.SIGALRM, functs.timeout)
            signal.alarm(1)

            receiverSocket, addr = ackSocket.accept()

            signal.alarm(0)
            connectionEstablished = True
            receivalTime = time.time()
            estimatedRoundTripTime = receivalTime - sendTime
            devRTT = 0
            receiverSocket.settimeout(timeout)
        except socket.timeout:
            retransmittedNum += 1
            continue

    #after connection is established, send all other packets        
    while True:
        try:
            ack = receiverSocket.recv(20)
            receivalTime = time.time()

            # unpack packet info
            ackSourcePort, ackDest, ackSequenceNumber,\
                ack_ackNumber, ackHeaderLength, ackValid,\
                ackLastPacket, ackWindowSize, ackContents = functs.unpackPacket(ack)

            log = str(datetime.datetime.now()) + " " + \
                  str(ackSourcePort) + " " + \
                  str(ackDest) + " " + \
                  str(ackSequenceNumber) + " " + \
                  str(ack_ackNumber) + "\n"

            # flags each packet in logFile
            if ackValid:
                log = log.strip("\n") + " ACK\n"
            if ackLastPacket:
                log = log.strip("\n") + " FIN\n"

            # If all is good and ack is valid, we continue
            if ack_ackNumber == ackNumber and ackValid:
                sampleRoundTripTime = receivalTime - sendTime
                estimatedRoundTripTime = estimatedRoundTripTime * 0.875 + sampleRoundTripTime * 0.125
                devRTT = 0.75 * devRTT + 0.25 * abs(sampleRoundTripTime - estimatedRoundTripTime)
                receiverSocket.settimeout(estimatedRoundTripTime + 4 * devRTT)

                #write log
                log = log.strip() + " " + str(estimatedRoundTripTime) + "\n"
                logF.write(log)
                if ackLastPacket:
                    break

                currText = sendFile.read(556)  # 576-20(for header)
                if currText == "":
                    lastPacket = True

                #update sequence Number and ackNumber
                sequenceNumber += 1
                ackNumber += 1

                #make and send next packet
                packet = functs.makePacket(ackPort, receiverPort,sequenceNumber, ackNumber, False,lastPacket, windowSize,currText)
                sendSocket.sendto(packet, (receiverIP, receiverPort))
                SentNum += 1 
                sendTime = time.time()

            else:
                logF.write(log)
                raise socket.timeout

        except socket.timeout: #need to retransmit
            packet = functs.makePacket(ackPort, receiverPort,sequenceNumber, ackNumber, False,lastPacket, windowSize,currText)
            sendSocket.sendto(packet, (receiverIP, receiverPort))
            SentNum += 1
            retransmittedNum += 1

    print("\n------------------Successfully Sent, AZP WORKS-----------------------")
    print("Total Num of Segments Sent = {} \n Number of Segments retransmitted= {}\n".format(str(SentNum),str(retransmittedNum)))








