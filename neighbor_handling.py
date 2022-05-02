from collections import deque
import frames


link_window = 4             #window size (48 default, 128 max)
sample = deque(8*[0],8)     #127-sized array record

print(sample)

last = 0

def HELLO_received(window, last_sqn, sqn):
    if last_sqn == -1:
        print("first received")
    
    if sqn == last_sqn:
        window.append(1)
    else:
        while sqn != last_sqn + 1:
            window.append(0)
            last_sqn = last_sqn + 1
        window.append(1)

    return sqn

last = HELLO_received(sample, last, 1)
last = HELLO_received(sample, last, 2)
last = HELLO_received(sample, last, 3)
last = HELLO_received(sample, last, 4)

print(sample)

def get_link_qual(window, size):
    msgs_received = 0
    for x in range(size):
        msgs_received = msgs_received + window[7 - x]
    quality = msgs_received/size
    return quality

link_qual = get_link_qual(sample, link_window)
print(link_qual*100,"%")
