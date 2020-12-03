#!/usr/bin/env python

#Receiver PART OF AZP -> Abdullah Zahid Protocol
#this builds a TCP-like protocol on top of UDP

import socket
import sys
import os
import socket
import signal
import time
import datetime
import functs #functs.py in the package which has necessary functions like ones to make a packet

if __name__ == '__main__':

    # Set command line args
    try:
        RecFileName,RecLogFileName= sys.argv[1],sys.argv[5]
        senderIP = socket.gethostbyname(sys.argv[3])
        senderPort,receiverPort = int(sys.argv[4]),int(sys.argv[2])
    except IndexError as TypeError:
        exit("All arguments not provided for receiving, please refer to explanation for correct usage")
    
    try:
        # Init UDP sockets for sending packets
        receiveSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        receiveSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        receiveSock.bind(("", receiverPort))

        # Init socket for getting acknowledgements 
        sendAckSock = socket.socket()
        sendAckSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    except socket.error:
        exit("Error creating sockets")

    try:
        receiveFile = open(RecFileName, 'wb')
    except IOError:
        exit("Error opening file:" + RecFileName)

    try:
        logFile = open(RecLogFileName, 'wb')
    except IOError:
        exit("Error opening log file: " + RecLogFileName)

    #keeps track of # of acks sent
    nextAckNumber = 0

    #get first packet and unpack it
    packet, addr = receiveSock.recvfrom(576)
    sourcePort, destPort, seqNum, ackNum, headerLen, ack, final, windowSize, contents = functs.unpackPacket(packet)

    CheckSum = functs.calculateCheckSum(packet)
    packetValid = CheckSum == 0 and nextAckNumber == ackNum

    if packetValid:
        receiveFile.write(contents)
        nextAckNumber += 1

    log = str(datetime.datetime.now()) + " " + str(sourcePort) + " " + str(destPort) + " " + str(seqNum) + " " + str(
        ackNum)
    logFile.write(log + "\n")

    # socket connection to send ACK
    sendAckSock.connect((senderIP, senderPort))
    ackSendPort = sendAckSock.getsockname()[1]
    ackPacket = functs.makePacket(ackSendPort, senderPort,
                                   seqNum, ackNum, packetValid,
                                   False, 1, "")
    sendAckSock.send(ackPacket)

    #connection has been established so let the inflow of packets
    #and outflow of ACK BEGINN

    while True:

        # Receive all other packets
        packet, addr = receiveSock.recvfrom(576)

        sourcePort, destPort, seqNum, ackNum, headerLen, \
            ack, final, windowSize, contents = functs.unpackPacket(packet)


        CheckSum = functs.calculateCheckSum(packet)

        #sometimes the checksum function reverses the checksum number for
        #some bytes, this is a fix.
        if CheckSum == 0xFFFF:
            CheckSum = 0

        log = str(datetime.datetime.now()) + " " + str(sourcePort) + " " + str(destPort) + " " + str(
            seqNum) + " " + str(ackNum)

        if final:
            log += " FIN"
        logFile.write(log + "\n")

        # if packet is all fine, ACK. if not: NACK
        packetValid = CheckSum == 0 and nextAckNumber == ackNum

        if packetValid:
            receiveFile.write(contents)
            nextAckNumber += 1

        ackPacket = functs.makePacket(ackSendPort, senderPort,
                                        seqNum, ackNum, packetValid,
                                        final, 1, "")
        sendAckSock.send(ackPacket)
        if final:
            break

    print("\n------------------Successfully Received, AZP WORKS-----------------------")
