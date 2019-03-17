import pytest
from piestats.update.roundmanager import RoundManager


def test_logfile_comparable():
  logfile1 = 'local:/srv/ssd3/dev/joe/gather7/logs/consolelog-19-03-16-04.txt'
  logfile2 = 'local:/srv/ssd3/dev/joe/gather7/logs/consolelog-19-03-16-05.txt'

  assert RoundManager.logfile_comparable(logfile1, logfile2) is True

  logfile3 = 'local:/srv/ssd3/dev/joe/gather7/logs/consolelog-19-03-16-04.txt'
  logfile4 = 'local:/srv/ssd3/dev/joe/gather8/logs/consolelog-19-03-16-05.txt'

  assert RoundManager.logfile_comparable(logfile3, logfile4) is False


def test_logfile_greater():
  logfile1 = 'local:/srv/ssd3/dev/joe/gather7/logs/consolelog-19-03-16-04.txt'
  logfile2 = 'local:/srv/ssd3/dev/joe/gather7/logs/consolelog-19-03-16-05.txt'

  assert RoundManager.logfile_greater(logfile1, logfile2) is False
  assert RoundManager.logfile_greater(logfile2, logfile1) is True

  logfile3 = 'local:/srv/ssd3/dev/joe/gather4/logs/consolelog-18-03-16-04.txt'
  logfile4 = 'local:/srv/ssd3/dev/joe/gather4/logs/consolelog-19-03-16-05.txt'

  assert RoundManager.logfile_greater(logfile3, logfile4) is False
  assert RoundManager.logfile_greater(logfile4, logfile3) is True

  # logfiles that are not comparable as they are not part of the same server
  with pytest.raises(ValueError):
    RoundManager.logfile_greater(logfile1, logfile3)
