import multiprocessing
import subprocess
import optparse
import tempfile
import shutil
import time
import sys
import os
import re

CFLAGS = '-O2 -std=gnu89 -faddress-sanitizer'
CXXFLAGS = CFLAGS
PYTHON = sys.executable
PROCESSORS = 1  #multiprocessing.cpu_count()
TEMP_DIR = os.getcwd() + '/test-spec-temp'

USAGE = 'usage: %prog [options] SPEC_PATH CLANG_BIN_DIR'

class WorkerProcess(multiprocessing.Process):
  def __init__(self, name, Q, spec_path, clang_bin_dir, runs, asan_opt):
    super(WorkerProcess, self).__init__()
    self.name = name
    self.Q = Q
    self.spec_path = spec_path
    self.clang_bin_dir = clang_bin_dir
    self.runs = runs
    self.asan_opt = asan_opt

  @classmethod
  def _get_time(cls, output):
    total = 0
    lines = output.split('\n')

    user_time = lines[1].split(' ')
    assert user_time[0] == 'user'
    total += float(user_time[1])

    sys_time = lines[2].split(' ')
    assert sys_time[0] == 'sys'
    total += float(sys_time[1])
    return total

  def create_links(self):
    src = self.spec_path + os.sep + self.name
    dst = self.temp_dir
    os.symlink(src + os.sep + 'run.sh', dst + os.sep + 'run.sh')
    for folder in ['src', 'data']:
      for file in os.listdir(src + os.sep + folder):
        os.symlink(src + os.sep + folder + os.sep + file, dst + os.sep + folder + os.sep + file)

  def create_temp_dir(self):
    self.temp_dir = tempfile.mkdtemp()
    os.makedirs(self.temp_dir + os.sep + 'src')
    os.makedirs(self.temp_dir + os.sep + 'data')
    self.create_links()

  def close(self):
    shutil.rmtree(self.temp_dir)

  def run(self):
    self.create_temp_dir()
    name = self.name
    init_path = self.temp_dir + os.sep
    src_path = init_path + 'src' + os.sep
    sys.stderr.write('start %s\n' % name)

    try:
      clang_bin = self.clang_bin_dir + '/clang'
      args = ['make']
      args.append('CC=' + self.clang_bin_dir + '/clang')
      args.append('CXX=' + self.clang_bin_dir + '/clang++')
      args.append('CFLAGS=' + CFLAGS + (' -mllvm "-asan-opt=%d"' % self.asan_opt))
      args.append('CXXFLAGS=' + CXXFLAGS + (' -mllvm "-asan-opt=%d"' % self.asan_opt))
      dev_null = open(os.devnull, 'w')
      subprocess.check_call(args, stderr=dev_null, stdout=dev_null, cwd=src_path)
      dev_null.close()

      times = []
      for _ in xrange(self.runs):
        out = subprocess.check_output(['time -p bash -c "' + init_path + 'run.sh' + ' > /dev/null 2> /dev/null"'], stderr=subprocess.STDOUT, shell=True, cwd=init_path)
        times.append(self._get_time(out))

      self.Q.put_nowait((name, times))
    except:
      self.Q.put_nowait((name, None))
      sys.stderr.write('fail %s\n' % name)
      self.close()
      raise
    sys.stderr.write('end %s\n' % name)
    self.close()

def find_spec_names(path):
  res = []
  for entry in os.listdir(path):
    prefix = path + '/' + entry
    if not os.path.exists(prefix + '/src'):
      continue
    if not os.path.exists(prefix + '/run.sh'):
      continue
    res.append(entry)
  return sorted(res)

if __name__ == '__main__':
  parser = optparse.OptionParser(usage=USAGE)
  parser.add_option("-O", "--opt", action="store_true", dest="opt", default=False,
                    help="Use ASan optimizations")
  parser.add_option("-r", "--runs", dest="runs", type="int", default=1,
                    help="Number of runs", metavar="RUNS")
  (options, args) = parser.parse_args()
  if len(args) < 2:
    parser.print_help()
    exit()

  spec_path = args[0]
  clang_bin_dir = args[1]

  names = find_spec_names(spec_path)
  #names = ['401.bzip2', '429.mcf', '433.milc', '456.hmmer', '458.sjeng', '462.libquantum', '470.lbm']
  #names = ['470.lbm', '462.libquantum']
  #names = ['470.lbm']
  #names = ['429.mcf']

  sys.stderr.write('Compiling and running the following:\n')
  for name in names:
    sys.stderr.write('%s\n' % name)
  sys.stderr.write('\n')

  if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

  handles = []
  Q = multiprocessing.Queue()
  for i in xrange(len(names)):
    p = WorkerProcess(names[i], Q, spec_path, clang_bin_dir, options.runs, 1 if options.opt else 0)
    handles.append(p)

  pos = 0
  while pos < len(names):
    working = pos - Q.qsize()
    if working < PROCESSORS:
      handles[pos].start()
      pos += 1
    else:
      time.sleep(0.01)

  all_times = {}
  for i in xrange(len(handles)):
    name, times = Q.get()
    if name not in times:
      all_times[name] = []
    all_times[name].extend(times)

  for name, time_list in all_times.iteritems():
    sys.stderr.write(name)
    total = 0
    num = 0
    for time in time_list:
      if time is None:
        sys.stderr.write('        fail')
      else:
        sys.stderr.write('        %.3f' % time)
        total += time
        num += 1
    if num:
      sys.stderr.write('        AVG %.3f' % (total / num))
    else:
      sys.stderr.write('        AVG NaN')
    sys.stderr.write('\n')
