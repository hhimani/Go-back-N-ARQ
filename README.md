# Go-back-N-ARQ
Name: Himani(hhimani)
Name Pavneet Singh Anand(panand4)


Automatic repeat request (ARQ) is a protocol for error control in data transmission. 
When the receiver detects an error in a packet, it automatically requests the transmitter to resend the packet.


Running the Sender/client

python Sender.py  <ip of server> <port of server> RFC123.txt <window> <mss> 

python sender.py localhost 7735 RFC123.txt 5 500
Running the Receiver/Server


python Receiver.py <port of server> RFC123.txt p 


python receiver.py 7735 RFC123.txt 0.05