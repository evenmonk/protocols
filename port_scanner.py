import threading
import socket

from datetime import datetime

start = datetime.now()
q = 0
ip = input("Enter ip : ")

def portscan(ip,port): 
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5) 

    try:
        connection = s.connect((ip,port)) 
        print('Port :', port, "is open.") 
        connection.close()
        q+=1   
    except:
        pass

if __name__ == "__main__":
    for element in range(1000): 
        t = threading.Thread(target=portscan, args = (ip, element))
        t.start() 
    if q==0:
        print("No opened ports")

    end = datetime.now()
    print('Time : {}'.format(end-start))