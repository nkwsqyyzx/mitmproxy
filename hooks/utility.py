import logging

def str2int(s):
    s = s.split('.')[0]
    return int(s or 0)


def create_logger(name, level=None):
    formatter = logging.Formatter("%(levelname).1s - %(asctime)s - %(name)-14s:%(message)s")
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    log = logging.getLogger(name)
    log.propagate = False
    if level is not None:
        log.setLevel(level)
    log.addHandler(ch)
    return log


def format_function(cls, f):
    full_class_name = cls.__module__ + '.' + cls.__class__.__name__
    return '{0}:{1}'.format(full_class_name, f.__name__)


logger = create_logger('ReadWriteHook', logging.WARN)


def debug_rewrite(f):
    def wrapper(cls, flow):
        address = flow.client_conn.address
        logger.info('{0}, before method {1}'.format(address, format_function(cls, f)))
        try:
            x = f(cls, flow)
            return x
        except Exception as e:
            logger.error('{0}, execute method {1} got error:{2}'.format(address, format_function(cls, f), e))
        finally:
            logger.info('{0}, after method {1}'.format(address, format_function(cls, f)))

    return wrapper


class ReadWriteHook(object):
    def __init__(self):
        self.logger = create_logger(self.__class__.__name__, logging.INFO)

    def host_check(self, flow):
        """:host to hook"""
        raise NotImplementedError()

    def rewrite_client_request(self, flow):
        """:modify client request"""
        raise NotImplementedError()

    def rewrite_server_response(self, flow):
        """:modify server response"""
        raise NotImplementedError()

    def respond(self, flow):
        """:return True to enable hook"""
        raise NotImplementedError()
