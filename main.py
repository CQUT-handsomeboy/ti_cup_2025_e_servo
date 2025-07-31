from servo import Servo, check_servo_status
from time import sleep
from queue import Queue
from threading import Thread
from dog import monitor_json_file_thread
from pid import DefaultPID
import cv2
import sys
import json
import logging
import numpy as np
from typing import List

sys.path.append("/home/orangepi/rknn3588-yolov8")
from detector import detect_thread  # type:ignore

with open("./config.json", "r", encoding="utf-8") as f:
    config = json.load(f)


def update_all_pids():
    while not config_q.empty():
        config = config_q.get()
    # pid1
    pid1.kp = config["pid1"]["kp"]
    pid1.ki = config["pid1"]["ki"]
    pid1.kd = config["pid1"]["kd"]
    pid1.I = 0
    pid1.error = 0
    pid1.prev_error = 0
    # pid2
    pid2.kp = config["pid2"]["kp"]
    pid2.ki = config["pid2"]["ki"]
    pid2.kd = config["pid2"]["kd"]
    pid2.I = 0
    pid2.error = 0
    pid2.prev_error = 0
    logging.info("pid update")

FRAME_WIDTH,FRAME_HEIGHT = 640,480

def track_target_thread(q: Queue):  # 控制舵机追踪的
    while True:
        data:dict = q.get()
        box:List[np.ndarray] = data["boxes"]
        x,y = (box[0] + box[2]) / 2,(box[1] + box[3]) / 2
        ctrl1 = pid1(x,FRAME_WIDTH/2)
        ctrl2 = pid2(y,FRAME_HEIGHT/2)
        # logging.info(f"💃-->{x},{y}")
        logging.info(f"🐕,{ctrl1} {ctrl2}")


pid1 = DefaultPID(
    kp=config["pid1"]["kp"],
    ki=config["pid1"]["ki"],
    kd=config["pid1"]["kd"],
)

pid2 = DefaultPID(
    kp=config["pid2"]["kp"],
    ki=config["pid2"]["ki"],
    kd=config["pid2"]["kd"],
)

if __name__ == "__main__":
    # servos = Servo("/dev/ttyUSB0")
    # check_servo_status(servos)
    detect_infoq = Queue()
    frameq = Queue()
    config_q = Queue()
    t1 = Thread(target=detect_thread, args=(detect_infoq, frameq))
    t2 = Thread(target=track_target_thread, args=(detect_infoq,))
    t3 = Thread(target=monitor_json_file_thread, args=(config_q,), daemon=True)
    t1.daemon = True
    t1.start()
    t2.daemon = True
    t2.start()
    t3.daemon = True
    t3.start()

    while True:
        frame = frameq.get()
        cv2.imshow("frame", frame)
        cv2.waitKey(1)
