from contextlib import contextmanager


class FileManager():

  def __init__(self):
    raise NotImplemented('Should be implemented')

  def get_file_paths(self):
    raise NotImplemented('Should be implemented')

  def get_files(self):
    raise NotImplemented('Should be implemented')

  def get_data(self):
    raise NotImplemented('Should be implemented')

  @contextmanager
  def initialize(self):
    yield
