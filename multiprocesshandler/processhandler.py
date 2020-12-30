import multiprocessing
from multiprocessing import Process
from threading import Timer
import time
import copy


class ProcessHandler:

    def __init__(self, timeout=None, interval=0.5, limit=None):
        self._procs = {}
        self._queue = []
        self._timeout = timeout
        self._interval = interval
        self._signal = True
        self._kill = False
        if limit is None or limit > multiprocessing.cpu_count():
            self._limit = multiprocessing.cpu_count() - 1
        else:
            self._limit = limit
        self._cycleFlag = True
        self._cycle = None
        self._cycles()

    def _cycles(self):
        self._process_release()
        if not self._kill:
            self._forward_queue()
            if self._signal or (self._signal == False and len(self._queue) > 0):
                self._cycle = Timer(self._interval, self._cycles)
                self._cycle.start()

    def stop(self, _kill=False):
        self._signal = False
        self._kill = _kill

    def queue(self, fn, **kwargs):
        if not self._signal:
            raise Exception('Trying to enqueue task after stop() is called')
        if self._limit > 0 and len(self._procs) >= self._limit:
            self._queue.append({
                'fn': fn,
                'kwargs': kwargs.get('kwargs')
            })
        else:
            self._spawn(fn=fn, kwargs=kwargs)

    def _spawn(self, fn, **kwargs):
        kwargs = kwargs.get('kwargs')
        p = Process(target=fn, kwargs=kwargs.get('kwargs'))
        p.daemon = False
        p.start()
        self._procs[p.pid] = {
            'proc': p,
            'started': time.time(),
            'kwargs': kwargs
        }

    def _forward_queue(self):
        i = 0
        for q in self._queue:
            if self._limit > 0 and len(self._procs) < self._limit:
                self._spawn(fn=q['fn'], kwargs=q)
                self._queue.pop(i)
            else:
                break
            i = i + 1

    def _process_release(self):
        procs = copy.copy(self._procs)
        for p in procs:
            if not self._procs[p]['proc'].is_alive():
                del (self._procs[p])  # self._procs.remove(p['proc'])
            else:
                if self._kill or not (self._timeout is None or int(time.time() - p['started']) > self._timeout):
                    self._procs[p]['proc'].terminate()
                    self._procs[p]['proc'].join()
                    del (self._procs[p])

    def check_workers(self):
        ret = False
        for p in procs:
            if self._procs[p]['proc'].is_alive():
                ret = True
                break;

        if (self._signal == False and len(self._queue) > 0) and not self._kill:
            ret = True

        return ret


