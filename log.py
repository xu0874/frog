import os
import logging
import datetime
import codecs

LOG_PATH = r'C:\Users\Administrator\Desktop\log'
LOG_KEEP_DAYS = 15
LOG_LEVEL = logging.DEBUG
LOG_FORMATTLER = "[%(asctime)s] %(name)s -<%(process)d>- %(levelname)s: %(message)s"

class DLogHandler(logging.FileHandler):
    """
    支持多进程的TimedRotatingFileHandler
    会写入当前进程号
    """
    def __init__(self, filename, encoding=None, delay=False):
        """
        filename 日志文件名
        delay 是否开启 OutSteam缓存
            True 表示开启缓存，OutStream输出到缓存，待缓存区满后，刷新缓存区，并输出缓存数据到文件。
            False表示不缓存，OutStrea直接输出到文件
        """
        self.prefix = filename
        # 正则匹配 年-月-日
        self.extMath = r"^\d{4}-\d{2}-\d{2}"
        # 日志文件日期格式
        self.suffix = "%Y-%m-%d"
        # 拼接文件路径 格式化字符串
        self.filefmt = os.path.join(LOG_PATH, "%s_%s.log" % (self.prefix, self.suffix))
        # 使用当前时间，格式化文件格式化字符串
        self.filepath = datetime.datetime.now().strftime(self.filefmt)
        try:
            # 如果日志文件夹不存在，则创建文件夹
            if not os.path.exists(LOG_PATH):
                os.makedirs(LOG_PATH)
        except Exception:
            print("创建文件夹失败")
            print("文件夹路径：" + LOG_PATH)
            pass

        if codecs is None:
            encoding = None

        logging.FileHandler.__init__(self, self.filepath, 'a+', encoding, delay)

    def isdatechange(self):
        """
        更改日志写入文件
        :return True 表示已更改，False 表示未更改
        """
        _filepath = datetime.datetime.now().strftime(self.filefmt)
        # 新日志文件名 不等于 旧日志文件名，则表示 已经到了日志切分的时候
        if _filepath != self.filepath:
            self.filepath = _filepath
            return True
        return False

    def tofile(self):
        """输出信息到日志文件，并删除多于保留个数的所有日志文件"""
        if self.stream:
            self.stream.close()
            # 关闭stream后必须重新设置stream为None，否则会造成对已关闭文件进行IO操作
            self.stream = None
        # delay 为False 表示 不OutStream不缓存数据 直接输出
        if not self.delay:
            self.stream = self._open()
        # 删除多于保留个数的所有日志文件
        if LOG_KEEP_DAYS > 0:
            for s in self.overfiles():
                print("删除", s)
                os.remove(s)

    def overfiles(self):
        """获得过期需要删除的日志文件"""
        filenames = os.listdir(LOG_PATH)
        result = []
        prefix = self.prefix + '_'
        plen = len(prefix)
        for filename in filenames:
            if filename[:plen] == prefix:
                # 日志日期 mylog_2017-03-19.log 中的 2017-03-19
                suffix = filename[plen: -4]
                # 匹配符合规则的日志文件，添加到result列表中
                if re.compile(self.extMath).match(suffix):
                    result.append(os.path.join(LOG_PATH, filename))
        result.sort()

        if len(result) <= LOG_KEEP_DAYS:
            result = []
        else:
            result = result[:(len(result) - LOG_KEEP_DAYS)]
        return result

    def emit(self, record):
        """发送一个日志记录
        覆盖FileHandler中的emit方法，logging会自动调用此方法"""
        try:
            if self.isdatechange():
                self.tofile()
            logging.FileHandler.emit(self, record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.handleError(record)
            self.handleError(e)


def getLogger(
        project, console=False):
    """
    获取统一配置的logger
    """
    fileHandler = DLogHandler(project)
    fileHandler.setFormatter(logging.Formatter(LOG_FORMATTLER))
    logger = logging.getLogger(project)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(fileHandler)
    if console:
        consoleStream = logging.StreamHandler()
        formatter = logging.Formatter("<pid:%(process)s> - %(levelname)s: %(message)s")
        consoleStream.setFormatter(formatter)
        logger.addHandler(consoleStream)
    return logger


