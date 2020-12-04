# AZ-Protocol

This report encapsulates the formation of the AZP, Abdullah Zahid Protocol. It is a TCP-like, reliable datagram transfer protocol over an unreliable network. I have coded this protocol in python using the sockets library to connect and create datagrams. I am pleased to say that the AZP works pretty well to deliver ordered and uncorrupted packets over an unreliable network. This protocol has been tested to run on linux systems (both centOS and ubuntu).

First let's see what the packets are designed to be like. First there is a 20-byte TCP-like header as shown below. Source and Destination parts contain the IPs and ports. Sequence Number is used to keep track of the packets sent and to keep them in order. ACK is used to let the sender know which packets have been received. Header length is kept constant at 20 bytes. The only Flag I have right now is the FIN flag which lets the receiver know that this is the last packet. Then checksum is used to validate the packets and see if they have been corrupted or tampered with.


|Source           | Destination       |                                                   											
|       Sequence Number               |																		
|       ACK Number                    |																		
|Header Length |FIN flag| Window Size |																		
| CheckSum     | Urgent pointer       |																		


Packets are made in functs.py using the makePacket function which makes the header as described above and then appends the contents of the packet to it. the file functs.py also contains a method for unpacking a packet to be used by the receiver to see the contents and meta data of the packet. It also implements a checksum function and a timeout function. 

The code for both sender and receiver are included. Let me walk you through its operation and how it works. 
*Note: i started off with outputting the logs to the terminal (stdout) but it was getting a bit messy with large files so I tabulated them in the logFiles

To invoke the sender, type in the terminal:
./senderAZP.py  fileToSend  receiverIP receiverPort portToGetACK logFileName

To invoke the receiver, type in the terminal:
./receiverAZP.py filenameToSave portToReceive senderIP senderPort receiverLogFileName

The arguments are pretty self-explanatory but the script will throw an error if they are missing or are incorrect.
The log files have rows where each column follows the following pattern:
	Time	SourcePort	 destPort	seqNumber    ACKNum    Flag(FIN Only)

Now, moving to the functionality. This transport protocol has been tested as a stop-and-wait (i.e. tested on window size of 1). Sender sends a packet and waits for ACK. if no ack and timeout happens (or gets a NACK) then the sender resends the packet and logs it as a retransmit.
The receiver waits for the first packet, once the first packet makes it through, a connection is established to send the ACKs. For each packet, the validity is checked through the checksum function in functs.py. If invalid packet, a NACK is sent. Once the sender sends all the packets, the final one is sent with a FIN tag on it. The receiver sees the FIN flag, writes it, sends FIN Ack and program exits. Once the FIN Ack is received by the sender, the sender program exits too. 
Suppose a packet is lost, then the timeout finishes and the sender assumes that the packet is lost. The timeout is adaptive and follows these equations (as shown in class):

sampleRoundTripTime = receivalTime - sendTime
estimatedRoundTripTime = estimatedRoundTripTime * 0.875 + sampleRoundTripTime * 0.125
devRTT = 0.75 * devRTT + 0.25 * abs(sampleRoundTripTime - estimatedRoundTripTime)

Upon testing with the linux diff, even for large files generated using base64 /dev/urandom | head -c 10000000 > testFileLarge.txt. The AZP works reasonably fast and with full reliability.
