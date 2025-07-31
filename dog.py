# -*- coding: utf-8 -*-
import json
import time
import logging
from pathlib import Path
from queue import Queue
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- 配置 ---
# 要监控的目录路径
WATCHED_DIR = "."
# 要监控的特定 JSON 文件名
TARGET_FILENAME = "config.json"
# 监控文件的完整路径
TARGET_FILE_PATH = Path(WATCHED_DIR) / TARGET_FILENAME

# --- 日志配置 ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class JSONFileHandler(FileSystemEventHandler):
    """
    自定义事件处理器，用于处理文件系统事件。
    当检测到目标文件修改时，会尝试加载并验证 JSON，
    如果合法，则将数据放入队列。
    """

    def __init__(self, queue: Queue):
        """
        初始化处理器。
        :param queue: 用于传递加载成功的 JSON 数据的队列。
        """
        super().__init__()
        self.queue = queue

    def on_modified(self, event):
        """
        当文件或目录被修改时触发。
        """
        # 检查是否是目标文件被修改
        if (
            not event.is_directory
            and Path(event.src_path).resolve() == TARGET_FILE_PATH.resolve()
        ):
            logger.info(f"检测到文件 {TARGET_FILENAME} 被修改。")
            self._load_and_queue_json()

    def _load_and_queue_json(self):
        """
        尝试加载 JSON 文件，如果合法则放入队列。
        """
        try:
            with open(TARGET_FILE_PATH, "r", encoding="utf-8") as f:
                # 尝试解析 JSON
                data = json.load(f)
            # 如果解析成功，将数据放入队列
            self.queue.put(data)
            logger.info(f"JSON 文件合法，数据已放入队列。")
        except json.JSONDecodeError as e:
            # 如果 JSON 不合法，记录错误
            logger.error(f"文件 {TARGET_FILENAME} 不是合法的 JSON 文件: {e}")
        except FileNotFoundError:
            # 如果文件在事件触发时被删除，记录警告
            logger.warning(f"文件 {TARGET_FILENAME} 未找到。")
        except Exception as e:
            # 捕获其他可能的 IO 错误
            logger.error(f"读取文件 {TARGET_FILENAME} 时发生错误: {e}")


def monitor_json_file_thread(queue: Queue):
    """
    监控线程执行的函数。
    """
    # 确保监控目录存在
    Path(WATCHED_DIR).mkdir(parents=True, exist_ok=True)

    # 创建观察者对象
    observer = Observer()

    # 创建事件处理器对象，并传入队列
    event_handler = JSONFileHandler(queue)

    # 将事件处理器与观察者关联，并指定要监控的目录
    # recursive=False 表示不监控子目录
    observer.schedule(event_handler, path=WATCHED_DIR, recursive=False)

    # 启动观察者
    observer.start()
    logger.info(
        f"开始在后台线程中监控目录 '{WATCHED_DIR}' 下的文件 '{TARGET_FILENAME}'..."
    )

    try:
        # 让观察者线程一直运行，等待文件系统事件
        # 主线程需要保持运行或使用其他机制来等待，否则程序会退出
        # 这里使用一个简单的循环，实际应用中可能需要更优雅的停止机制
        while getattr(monitor_json_file_thread, "keep_running", True):
            time.sleep(1)
    except Exception as e:
        logger.error(f"监控线程中发生未预期错误: {e}")
    finally:
        observer.stop()
        observer.join()  # 等待观察者线程完全停止
        logger.info("监控线程已停止。")


if __name__ == "__main__":
    config_queue = Queue()
    watchdog_thread = Thread(
        target=monitor_json_file_thread, args=(config_queue,), daemon=True
    )
    watchdog_thread.start()

    while True:
        data = config_queue.get()
