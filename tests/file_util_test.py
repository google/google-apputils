#!/usr/bin/env python
# Copyright 2007 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unittest for common file utilities."""



import __builtin__
import errno
import os
import posix
import pwd
import shutil
import stat
import tempfile

import mox

from google.apputils import basetest
from google.apputils import file_util
import gflags as flags


FLAGS = flags.FLAGS

# pylint is dumb about mox:
# pylint: disable=no-member


class FileUtilTest(basetest.TestCase):

  def testHomeDir(self):
    self.assertEqual(file_util.HomeDir(), pwd.getpwuid(os.geteuid()).pw_dir)
    self.assertEqual(file_util.HomeDir(0), pwd.getpwuid(0).pw_dir)
    self.assertEqual(file_util.HomeDir('root'), pwd.getpwnam('root').pw_dir)



class FileUtilTempdirTest(basetest.TestCase):

  def setUp(self):
    self.temp_dir = tempfile.mkdtemp()
    self.file_path = self.temp_dir + 'sample.txt'
    self.sample_contents = 'Random text: aldmkfhjwoem103u74.'
    # To avoid confusion in the mode tests.
    self.prev_umask = posix.umask(0)

  def tearDown(self):
    shutil.rmtree(self.temp_dir)
    posix.umask(self.prev_umask)

  def testWriteOverwrite(self):
    file_util.Write(self.file_path, 'original contents')
    file_util.Write(self.file_path, self.sample_contents)
    with open(self.file_path) as fp:
      self.assertEquals(fp.read(), self.sample_contents)

  def testWriteExclusive(self):
    file_util.Write(self.file_path, 'original contents')
    self.assertRaises(OSError, file_util.Write, self.file_path,
                      self.sample_contents, overwrite_existing=False)

  def testWriteMode(self):
    mode = 0744
    file_util.Write(self.file_path, self.sample_contents, mode=mode)
    s = os.stat(self.file_path)
    self.assertEqual(stat.S_IMODE(s.st_mode), mode)

  def testAtomicWriteSuccessful(self):
    file_util.AtomicWrite(self.file_path, self.sample_contents)
    with open(self.file_path) as fp:
      self.assertEquals(fp.read(), self.sample_contents)

  def testAtomicWriteMode(self):
    mode = 0745
    file_util.AtomicWrite(self.file_path, self.sample_contents, mode=mode)
    s = os.stat(self.file_path)
    self.assertEqual(stat.S_IMODE(s.st_mode), mode)


class FileUtilMoxTestBase(basetest.TestCase):

  def setUp(self):
    self.mox = mox.Mox()
    self.sample_contents = 'Contents of the file'
    self.file_path = '/path/to/some/file'
    self.fd = 'a file descriptor'

  def tearDown(self):
    # In case a test fails before it gets to the unset line.
    self.mox.UnsetStubs()


class FileUtilMoxTest(FileUtilMoxTestBase):

  def testListDirPath(self):
    self.mox.StubOutWithMock(os, 'listdir')
    dir_contents = ['file1', 'file2', 'file3', 'directory1', 'file4',
                    'directory2']
    os.listdir('/path/to/some/directory').AndReturn(dir_contents)
    self.mox.ReplayAll()
    self.assertListEqual(file_util.ListDirPath('/path/to/some/directory'),
                         ['%s/%s' % ('/path/to/some/directory', entry)
                          for entry in dir_contents])
    self.mox.VerifyAll()

  def testSuccessfulRead(self):
    file_handle = self.mox.CreateMockAnything()
    self.mox.StubOutWithMock(__builtin__, 'open', use_mock_anything=True)
    open(self.file_path).AndReturn(file_handle)
    file_handle.__enter__().AndReturn(file_handle)
    file_handle.read().AndReturn(self.sample_contents)
    file_handle.__exit__(None, None, None)

    self.mox.ReplayAll()
    try:
      self.assertEquals(file_util.Read(self.file_path), self.sample_contents)
      self.mox.VerifyAll()
    finally:
      # Because we mock out the built-in open() function, which the unittest
      # library depends on, we need to make sure we revert it before leaving the
      # test, otherwise any test failures will cause further internal failures
      # and yield no meaningful error output.
      self.mox.ResetAll()
      self.mox.UnsetStubs()

  def testWriteGroup(self):
    self.mox.StubOutWithMock(os, 'open')
    self.mox.StubOutWithMock(os, 'write')
    self.mox.StubOutWithMock(os, 'close')
    self.mox.StubOutWithMock(os, 'chown')
    gid = 'new gid'
    os.open(self.file_path, os.O_WRONLY | os.O_TRUNC | os.O_CREAT,
            0666).AndReturn(self.fd)
    os.write(self.fd, self.sample_contents)
    os.close(self.fd)
    os.chown(self.file_path, -1, gid)
    self.mox.ReplayAll()
    file_util.Write(self.file_path, self.sample_contents, gid=gid)
    self.mox.VerifyAll()


class AtomicWriteMoxTest(FileUtilMoxTestBase):

  def setUp(self):
    super(AtomicWriteMoxTest, self).setUp()
    self.mox.StubOutWithMock(tempfile, 'mkstemp')
    self.mox.StubOutWithMock(os, 'write')
    self.mox.StubOutWithMock(os, 'close')
    self.mox.StubOutWithMock(os, 'chmod')
    self.mox.StubOutWithMock(os, 'rename')
    self.mox.StubOutWithMock(os, 'remove')
    self.mode = 'new permissions'
    self.gid = 'new gid'
    self.temp_filename = '/some/temp/file'
    self.os_error = OSError('A problem renaming!')

    tempfile.mkstemp(dir='/path/to/some').AndReturn(
        (self.fd, self.temp_filename))
    os.write(self.fd, self.sample_contents)
    os.close(self.fd)
    os.chmod(self.temp_filename, self.mode)

  def tearDown(self):
    self.mox.UnsetStubs()

  def testAtomicWriteGroup(self):
    self.mox.StubOutWithMock(os, 'chown')
    os.chown(self.temp_filename, -1, self.gid)
    os.rename(self.temp_filename, self.file_path)
    self.mox.ReplayAll()
    file_util.AtomicWrite(self.file_path, self.sample_contents,
                          mode=self.mode, gid=self.gid)
    self.mox.VerifyAll()

  def testAtomicWriteGroupError(self):
    self.mox.StubOutWithMock(os, 'chown')
    os.chown(self.temp_filename, -1, self.gid).AndRaise(self.os_error)
    os.remove(self.temp_filename)
    self.mox.ReplayAll()
    self.assertRaises(OSError, file_util.AtomicWrite, self.file_path,
                      self.sample_contents, mode=self.mode, gid=self.gid)

    self.mox.VerifyAll()

  def testRenamingError(self):
    os.rename(self.temp_filename, self.file_path).AndRaise(self.os_error)
    os.remove(self.temp_filename)
    self.mox.ReplayAll()
    self.assertRaises(OSError, file_util.AtomicWrite, self.file_path,
                      self.sample_contents, mode=self.mode)
    self.mox.VerifyAll()

  def testRenamingErrorWithRemoveError(self):
    extra_error = OSError('A problem removing!')
    os.rename(self.temp_filename, self.file_path).AndRaise(self.os_error)
    os.remove(self.temp_filename).AndRaise(extra_error)
    self.mox.ReplayAll()
    try:
      file_util.AtomicWrite(self.file_path, self.sample_contents,
                            mode=self.mode)
    except OSError as e:
      self.assertEquals(str(e),
                        'A problem renaming!. Additional errors cleaning up: '
                        'A problem removing!')
    else:
      raise self.failureException('OSError not raised by AtomicWrite')
    self.mox.VerifyAll()


class TemporaryFilesMoxTest(FileUtilMoxTestBase):

  def testTemporaryFileWithContents(self):
    contents = 'Inspiration!'
    with file_util.TemporaryFileWithContents(contents) as temporary_file:
      filename = temporary_file.name
      contents_read = open(temporary_file.name).read()
      self.assertEqual(contents_read, contents)

    # Ensure that the file does not exist.
    self.assertFalse(os.path.exists(filename))


class TemporaryDirsMoxTest(FileUtilMoxTestBase):

  def testTemporaryDirectoryWithException(self):
    def Inner(accumulator):
      with file_util.TemporaryDirectory(base_path=FLAGS.test_tmpdir) as tmpdir:
        self.assertTrue(os.path.isdir(tmpdir))
        accumulator.append(tmpdir)
        raise Exception('meh')

    temp_dirs = []
    self.assertRaises(Exception, Inner, temp_dirs)
    # Ensure that the directory is removed on exit even when exceptions happen.
    self.assertEquals(len(temp_dirs), 1)
    self.assertFalse(os.path.isdir(temp_dirs[0]))

  def testTemporaryDirectory(self):
    with file_util.TemporaryDirectory(base_path=FLAGS.test_tmpdir) as temp_dir:
      self.assertTrue(os.path.isdir(temp_dir))

    # Ensure that the directory is removed on exit.
    self.assertFalse(os.path.isdir(temp_dir))


class MkDirsMoxTest(FileUtilMoxTestBase):

  # pylint is dumb about mox:
  # pylint: disable=maybe-no-member

  def setUp(self):
    super(MkDirsMoxTest, self).setUp()
    self.mox.StubOutWithMock(os, 'mkdir')
    self.mox.StubOutWithMock(os, 'chmod')
    self.mox.StubOutWithMock(os.path, 'isdir')
    self.dir_tree = ['/path', 'to', 'some', 'directory']

  def tearDown(self):
    self.mox.UnsetStubs()

  def testNoErrorsAbsoluteOneDir(self):
    # record, replay
    os.mkdir('/foo')
    self.mox.ReplayAll()
    # test, verify
    file_util.MkDirs('/foo')
    self.mox.VerifyAll()

  def testNoErrorsAbsoluteOneDirWithForceMode(self):
    # record, replay
    os.mkdir('/foo')
    os.chmod('/foo', 0707)
    self.mox.ReplayAll()
    # test, verify
    file_util.MkDirs('/foo', force_mode=0707)
    self.mox.VerifyAll()

  def testNoErrorsExistingDirWithForceMode(self):
    exist_error = OSError(errno.EEXIST, 'This string not used')
    # record, replay
    os.mkdir('/foo').AndRaise(exist_error)
    # no chmod is called since the dir exists
    os.path.isdir('/foo').AndReturn(True)
    self.mox.ReplayAll()
    # test, verify
    file_util.MkDirs('/foo', force_mode=0707)
    self.mox.VerifyAll()

  def testNoErrorsAbsoluteSlashDot(self):
    # record, replay
    os.mkdir('/foo')
    self.mox.ReplayAll()
    # test, verify
    file_util.MkDirs('/foo/.')
    self.mox.VerifyAll()

  def testNoErrorsAbsoluteExcessiveSlashDot(self):
    """See that normpath removes irrelevant .'s in the path."""
    # record, replay
    os.mkdir('/foo')
    os.mkdir('/foo/bar')
    self.mox.ReplayAll()
    # test, verify
    file_util.MkDirs('/./foo/./././bar/.')
    self.mox.VerifyAll()

  def testNoErrorsAbsoluteTwoDirs(self):
    # record, replay
    os.mkdir('/foo')
    os.mkdir('/foo/bar')
    self.mox.ReplayAll()
    # test, verify
    file_util.MkDirs('/foo/bar')
    self.mox.VerifyAll()

  def testNoErrorsPartialTwoDirsWithForceMode(self):
    exist_error = OSError(errno.EEXIST, 'This string not used')
    # record, replay
    os.mkdir('/foo').AndRaise(exist_error)  # /foo exists
    os.path.isdir('/foo').AndReturn(True)
    os.mkdir('/foo/bar')  # bar does not
    os.chmod('/foo/bar', 0707)
    self.mox.ReplayAll()
    # test, verify
    file_util.MkDirs('/foo/bar', force_mode=0707)
    self.mox.VerifyAll()

  def testNoErrorsRelativeOneDir(self):
    # record, replay
    os.mkdir('foo')
    self.mox.ReplayAll()
    # test, verify
    file_util.MkDirs('foo')
    self.mox.VerifyAll()

  def testNoErrorsRelativeTwoDirs(self):
    # record, replay
    os.mkdir('foo')
    os.mkdir('foo/bar')
    self.mox.ReplayAll()
    # test, verify
    file_util.MkDirs('foo/bar')
    self.mox.VerifyAll()

  def testDirectoriesExist(self):
    exist_error = OSError(errno.EEXIST, 'This string not used')
    # record, replay
    for i in range(len(self.dir_tree)):
      path = os.path.join(*self.dir_tree[:i+1])
      os.mkdir(path).AndRaise(exist_error)
      os.path.isdir(path).AndReturn(True)
    self.mox.ReplayAll()
    # test, verify
    file_util.MkDirs(os.path.join(*self.dir_tree))
    self.mox.VerifyAll()

  def testFileInsteadOfDirectory(self):
    exist_error = OSError(errno.EEXIST, 'This string not used')
    path = self.dir_tree[0]
    # record, replay
    os.mkdir(path).AndRaise(exist_error)
    os.path.isdir(path).AndReturn(False)
    self.mox.ReplayAll()
    # test, verify
    self.assertRaises(OSError, file_util.MkDirs, os.path.join(*self.dir_tree))
    self.mox.VerifyAll()

  def testNonExistsError(self):
    non_exist_error = OSError(errno.ETIMEDOUT, 'This string not used')
    path = self.dir_tree[0]
    # record, replay
    os.mkdir(path).AndRaise(non_exist_error)
    self.mox.ReplayAll()
    # test, verify
    self.assertRaises(OSError, file_util.MkDirs, os.path.join(*self.dir_tree))
    self.mox.VerifyAll()


class RmDirsTestCase(mox.MoxTestBase):

  def testRmDirs(self):
    test_sandbox = os.path.join(FLAGS.test_tmpdir, 'test-rm-dirs')
    test_dir = os.path.join(test_sandbox, 'test', 'dir')

    os.makedirs(test_sandbox)
    with open(os.path.join(test_sandbox, 'file'), 'w'):
      pass
    os.makedirs(test_dir)
    with open(os.path.join(test_dir, 'file'), 'w'):
      pass

    file_util.RmDirs(test_dir)

    self.assertFalse(os.path.exists(os.path.join(test_sandbox, 'test')))
    self.assertTrue(os.path.exists(os.path.join(test_sandbox, 'file')))

    shutil.rmtree(test_sandbox)

  def testRmDirsForNonExistingDirectory(self):
    self.mox.StubOutWithMock(os, 'rmdir')
    os.rmdir('path/to')
    os.rmdir('path')

    self.mox.StubOutWithMock(shutil, 'rmtree')
    shutil.rmtree('path/to/directory').AndRaise(
        OSError(errno.ENOENT, "No such file or directory 'path/to/directory'"))

    self.mox.ReplayAll()

    file_util.RmDirs('path/to/directory')
    self.mox.VerifyAll()

  def testRmDirsForNonExistingParentDirectory(self):
    self.mox.StubOutWithMock(os, 'rmdir')
    os.rmdir('path/to').AndRaise(
        OSError(errno.ENOENT, "No such file or directory 'path/to'"))
    os.rmdir('path')

    self.mox.StubOutWithMock(shutil, 'rmtree')
    shutil.rmtree('path/to/directory').AndRaise(
        OSError(errno.ENOENT, "No such file or directory 'path/to/directory'"))

    self.mox.ReplayAll()

    file_util.RmDirs('path/to/directory')
    self.mox.VerifyAll()

  def testRmDirsForNotEmptyDirectory(self):
    self.mox.StubOutWithMock(os, 'rmdir')
    os.rmdir('path/to').AndRaise(
        OSError(errno.ENOTEMPTY, 'Directory not empty', 'path/to'))

    self.mox.StubOutWithMock(shutil, 'rmtree')
    shutil.rmtree('path/to/directory')

    self.mox.ReplayAll()

    file_util.RmDirs('path/to/directory')
    self.mox.VerifyAll()

  def testRmDirsForPermissionDeniedOnParentDirectory(self):
    self.mox.StubOutWithMock(os, 'rmdir')
    os.rmdir('path/to').AndRaise(
        OSError(errno.EACCES, 'Permission denied', 'path/to'))

    self.mox.StubOutWithMock(shutil, 'rmtree')
    shutil.rmtree('path/to/directory')

    self.mox.ReplayAll()

    file_util.RmDirs('path/to/directory')
    self.mox.VerifyAll()

  def testRmDirsWithSimplePath(self):
    self.mox.StubOutWithMock(shutil, 'rmtree')
    shutil.rmtree('directory')

    self.mox.ReplayAll()

    file_util.RmDirs('directory')
    self.mox.VerifyAll()


if __name__ == '__main__':
  basetest.main()
