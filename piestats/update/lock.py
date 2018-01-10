from tempfile import gettempdir
from contextlib import contextmanager
import os
import fcntl


@contextmanager
def acquire_lock():
  '''Try to only let one instance of the updater script run at once'''
  tmpdir = gettempdir()

  # If we can't determine what tmpdir to use (normally should be /tmp) just bail
  if not tmpdir:
    yield
    return

  lockfile = os.path.join(tmpdir, '.pystats.lock')

  # Try opening it. If we can't just bail
  try:
    handle = open(lockfile, 'w')
  except IOError:
    yield
    return

  print 'Acquiring lock (ensuring only one update is running at once)'

  try:
    fcntl.lockf(handle, fcntl.LOCK_EX)

  # This should never fail and instead just block if another instance has the lock,
  # but in case it does fail, don't bail the updater
  except Exception as e:
    print 'Failed acquiring lock: %s' % e

  try:
    yield
  finally:
    try:
      handle.close()
    except:
      pass

    # Don't leave the file hanging around after us
    try:
      os.unlink(lockfile)
    except OSError:
      pass
