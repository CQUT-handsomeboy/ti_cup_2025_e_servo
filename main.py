from servo import Servo, check_servo_status
from time import sleep
from queue import Queue
from threading import Thread
from dog import monitor_json_file_thread
from pid import IncreasementalPID
import cv2
import sys
import json
import logging

sys.path.append("/home/orangepi/rknn3588-yolov8")
from detector import detect_thread  # type:ignore

with open("./config.json", "r", encoding="utf-8") as f:
    config = json.load(f)


def update_all_pids():
    while not config_q.empty():
        config = config_q.get()
    pid1.kp = config["pid1"]["kp"]
    pid1.ki = config["pid1"]["ki"]
    pid1.kd = config["pid1"]["kd"]
    logging.info("pid update")


pid1 = IncreasementalPID(
    kp=config["pid1"]["kp"],
    ki=config["pid1"]["ki"],
    kd=config["pid1"]["kd"],
)

if __name__ == "__main__":
    # servos = Servo("/dev/ttyUSB0")
    # check_servo_status(servos)
    detect_infoq = Queue()
    frameq = Queue()
    config_q = Queue()
    t1 = Thread(target=detect_thread, args=(detect_infoq, frameq))
    t3 = Thread(target=monitor_json_file_thread, args=(config_q,), daemon=True)
    t1.daemon = True
    t1.start()
    t3.daemon = True
    t3.start()

    while True:
        frame = frameq.get()
        cv2.rectangle(frame, (240, 0), (480, 375), (0, 0, 255), 2)
        cv2.imshow("frame", frame)
        cv2.waitKey(1)
