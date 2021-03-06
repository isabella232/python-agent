import logging
from cattle import Config

log = logging.getLogger('concurrency')

__all__ = ['Queue', 'Empty', 'Full', 'Worker', 'run', 'spawn', 'blocking']

if Config.is_eventlet():
    import eventlet
    eventlet.monkey_patch()
    from eventlet.queue import Queue, Empty, Full
    from eventlet import tpool

    pool = eventlet.GreenPool(size=Config.workers() * 2)

    class Worker:
        def __init__(self, target=None, args=None):
            self._target = target
            self._args = args

        def start(self):
            pool.spawn_n(self._target, *self._args)

    log.info('Using eventlet')

    port = Config.eventlet_backdoor()

    if port:
        from eventlet import backdoor
        log.info('Launching eventlet backdoor on port %s', port)
        eventlet.spawn(backdoor.backdoor_server,
                       eventlet.listen(('localhost', port)))
elif Config.is_multi_proc():
    from Queue import Empty, Full
    from multiprocessing import Queue, Process
    Worker = Process

    log.info('Using multiprocessing')
elif Config.is_multi_thread():
    from Queue import Queue, Empty, Full
    from threading import Thread
    Worker = Thread

    log.info('Using threading')
else:
    raise Exception('Could not determine concurrency style set '
                    'CATTLE_AGENT_MULTI to eventlet, thread, or '
                    'proc')


def spawn(**kw):
    p = Worker(**kw)
    p.daemon = True
    p.start()
    return p


def run(method, *args):
    if Config.is_eventlet():
        pool.spawn(method, *args).wait()
    else:
        method(*args)


def blocking(method, *args, **kw):
    if Config.is_eventlet():
        return tpool.execute(method, *args, **kw)
    else:
        return method(*args, **kw)
