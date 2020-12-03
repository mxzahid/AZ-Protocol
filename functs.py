import socket
import struct

headerFormat = "!HHIIBBHHH"
headerSize = 5


def calculateCheckSum(data):
    dataLen = len(data)
    # length is odd
    if (dataLen & 1):
        dataLen -= 1
        sum = ord(data[dataLen])
    else:
        sum = 0

    # iterate through chars 2 at a time and sum byte values
    while dataLen > 0:
        dataLen -= 2
        sum += (ord(data[dataLen + 1]) << 8) + ord(data[dataLen])

    # Wrap overflow
    sum = (sum >> 16) + (sum & 0xffff)

    result = (~ sum) & 0xffff  # 1's complement
    result = result >> 8 | ((result & 0xff) << 8)  # Swap bytes
    return result

def makePacket(sourcePort, destPort,
                seqNum, ackNum, ack,
                final, windowSize,
                contents):
    if final:
        flags = 1
    else:
        flags = 0

    if ack:
        flags += 16

    header = struct.pack(headerFormat, sourcePort,
                         destPort, seqNum, ackNum,
                         headerSize, flags,
                         windowSize, 0, 0)

    check = calculateCheckSum(header + contents)

    header = struct.pack(headerFormat, sourcePort,
                         destPort, seqNum, ackNum,
                         headerSize, flags,
                         windowSize, check, 0)

    return header + contents


def unpackPacket(segment):
    header = segment[:20]
    packetSourcePort, packetDestPort, packetSeqNum, \
    packetAckNum, packetHeaderLen, packetFlags, \
    packetWindowSize, packetCheckSum, \
    packetUrgent = struct.unpack(headerFormat, header)

    packetAck = (packetFlags >> 4) == 1
    packetFinal = int(packetFlags % 2 == 1)
    packetContents = segment[20:]

    return packetSourcePort, packetDestPort, \
           packetSeqNum, packetAckNum, packetHeaderLen, \
           packetAck, packetFinal, packetWindowSize, \
           packetContents


def timeout(signum, frame):
    raise socket.timeout