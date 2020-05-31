from piestats.update.applyevents import ApplyEvents

from setproctitle import setproctitle
import multiprocessing
import queue
import os


class MultiProcApplyEvents(ApplyEvents):

  def __init__(self, *args, **kwargs):
    super(MultiProcApplyEvents, self).__init__(*args, **kwargs)

    self.workers = []
    self.kill_queue = multiprocessing.JoinableQueue()
    self.kill_event = multiprocessing.Event()

  def kill_queue_worker(self, worker_number, original_ppid):
    ''' Pull kills off our queue and apply them using the parent's apply_kill method '''
    setproctitle('Piestats Kill Queue Worker %d' % worker_number)

    while True:
      if os.getppid() != original_ppid:
        print('Parent changed. Worker %d dying.' % worker_number)
        return

      try:
        kill, incr = self.kill_queue.get(True, .1)
      except queue.Empty:
        if self.kill_event.is_set():
          return
        else:
          continue

      super(MultiProcApplyEvents, self).apply_kill(kill, incr)
      self.kill_queue.task_done()

  def apply_kill(self, kill, incr=1):
    ''' Catch parent's call to apply kill, and add the item to our queue '''
    self.kill_queue.put((kill, incr))

  def start_procs(self):
    ''' Start all our worker procs '''
    original_pid = os.getpid()

    for worker_number in range(multiprocessing.cpu_count()):
      worker = multiprocessing.Process(target=self.kill_queue_worker, args=(worker_number, original_pid))
      worker.daemon = True
      worker.start()
      self.workers.append(worker)

  def teardown_procs(self):
    ''' Stop operations '''

    self.kill_queue.join()
    self.kill_event.set()
    for worker in self.workers:
      worker.join()
    self.workers = []

  def __enter__(self, *args):
    self.start_procs()
    return self

  def __exit__(self, *args):
    self.teardown_procs()
