import sys
import socket
import time
import struct
import threading
import os

N = 20
lock = threading.Lock()
packets_to_send = []
prev_seq = -1
packets_sent_not_acked = 0

def validate_checksum(data):
    s = 0
    for i in range(0, len(data), 2):
        if i + 1 < len(data):
            w = ord(data[i]) + (ord(data[i + 1]) << 8)
            k = s + w
            s = (k & 0xffff) + (k >> 16)
    return ~s & 0xffff

def create_packet(seq,data):
    checksum = validate_checksum(data)
    header = struct.pack('!IHH',seq, checksum, 21845)
    return header + data

def create_packets(filename,MSS):
    global packets_to_send
    if os.path.isfile(filename):
        content = ''
        seq = 0
        f = open(filename, 'rb')
        byte = f.read(1)
        content += byte
        while content != '':
            if len(content) == MSS or byte == '':
                packets_to_send.append(create_packet(seq,content))
                content = ''
                seq += 1
            byte = f.read(1)
            content += byte
        packets_to_send.append(create_packet(seq, '!E!O!F!'))
        f.close()
    else:
        print 'File not present.\n'
        sys.exit()

def rdt_send(addr, client_socket, N):
    global packets_to_send, prev_seq, packets_sent_not_acked
    num_of_packets = len(packets_to_send)
    time_record = [None]*num_of_packets
    while (prev_seq + 1) < num_of_packets:
        lock.acquire()
        if packets_sent_not_acked < N and ((prev_seq + packets_sent_not_acked + 1) < num_of_packets):
            client_socket.sendto(packets_to_send[prev_seq + packets_sent_not_acked + 1], addr)
            time_record[prev_seq + packets_sent_not_acked + 1] = time.time()
            packets_sent_not_acked += 1
        if packets_sent_not_acked > 0:
            # Taking 0.1 as RTO
            if (time.time() - time_record[prev_seq + 1]) > 0.1:
                print 'Time out, Sequence Number =' + str(prev_seq+1)
                packets_sent_not_acked = 0
        lock.release()

def get_ack_attr(ack_packet):
    ack = struct.unpack('!IHH', ack_packet)
    seq_num = ack[0]
    is_valid = False
    if ack[1] == 0 and ack[2] == 43690:
        is_valid = True
    else:
        print 'Invalid Header Format'
    return is_valid, seq_num

def get_acks(client_socket):
    global prev_seq, packets_sent_not_acked, packets_to_send
    try:
        while (prev_seq + 1) < len(packets_to_send):
            if packets_sent_not_acked > 0:
                ack_packet, addr = client_socket.recvfrom(2048)
                is_valid, seq_num = get_ack_attr(ack_packet)
                lock.acquire()
                if is_valid:
                    if prev_seq+1 == seq_num:
                        prev_seq += 1
                        packets_sent_not_acked -= 1
                    else:
                        packets_sent_not_acked = 0
                else:
                    packets_sent_not_acked = 0
                lock.release()
    except:
        print "Server connection closed"
        client_socket.close()
        sys.exit()

def main():
    global N
    host_name = '192.168.172.1'
    server_port = 7735
    filename = 'RFC123.txt'
    MSS = 500
    if len(sys.argv) > 1:
        host_name = sys.argv[1]
        server_port = int(sys.argv[2])
        filename = sys.argv[3]
        N = int(sys.argv[4])
        MSS = int(sys.argv[5])
    addr = (host_name, server_port)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    port = 8282
    client_socket.bind(( '0.0.0.0' , port))
    print 'Client Port :-' + str(port) + 'Server Address :- ' +str(addr)
    create_packets(filename,MSS)
    start = time.time()
    get_acks_thread = threading.Thread(target=get_acks, args=(client_socket,))
    rdt_send_thread = threading.Thread(target=rdt_send,args=(addr, client_socket, N))
    get_acks_thread.start()
    rdt_send_thread.start()
    get_acks_thread.join()
    rdt_send_thread.join()
    print 'Time for file transfer:' + str(time.time() - start)
    if client_socket:
        client_socket.close()

if __name__ == '__main__':
    main()
