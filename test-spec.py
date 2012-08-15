import multiprocessing
import subprocess
import time
import sys
import os

from optparse import OptionParser

CFLAGS = '-O2 -std=gnu89 -fmemory-access-instrumentation'
CFLAGS += ' ' + os.getcwd() + '/rtccounter/librtccounter.a'  
PYTHON = sys.executable
COMBINE_MSCC_PATH = 'combine-mscc-reports.py'
PROCESSORS = multiprocessing.cpu_count()
TEMP_DIR = os.getcwd() + '/test-spec-temp'
OPTIMIZATIONS = ['opt1', 'opt2', 'opt3']
#OPTIMIZATIONS = ['optimize-fast-memory-checks', 'optimize-identical-ls-checks', 'optimize-implied-fast-ls-checks']

class WorkerProcess(multiprocessing.Process):
  def __init__(self, name, Q, execute, prefix, use_old, spec_path, clang_bin_dir):
    super(WorkerProcess, self).__init__()
    self.name = name
    self.execute = execute
    self.Q = Q
    self.prefix = prefix
    self.use_old = use_old
    self.spec_path = spec_path
    self.clang_bin_dir = clang_bin_dir

  def run(self):
    name = self.name
    init_path = self.spec_path + '/' + name + '/'
    src_path = init_path + 'src/'
    out_path = self.prefix + name + '-raw.txt'
    clean_path = self.prefix + name + '.txt'
    if os.path.exists(clean_path) and self.use_old:
      sys.stderr.write('found old %s\n' % name)
      self.Q.put_nowait(open(clean_path).read())
      return

    sys.stderr.write('start %s\n' % name)

    try:
      clang_bin = self.clang_bin_dir + '/clang'
      subprocess.check_call(['make', 'CC=' + clang_bin, 'CFLAGS=' + CFLAGS], stderr=subprocess.STDOUT, stdout=open(out_path, 'w'), cwd=src_path)
      if self.execute:
        subprocess.check_call([init_path + 'run.sh'], stderr=open(out_path, 'a'), stdout=subprocess.PIPE, shell=True, cwd=init_path)

      subprocess.check_call([PYTHON, COMBINE_MSCC_PATH], stdin = open(out_path), stdout=open(clean_path, 'w'))
      self.Q.put_nowait(open(clean_path).read())
      os.remove(out_path)
    except:
      self.Q.put_nowait('')
      sys.stderr.write('fail %s\n' % name)
      raise
    sys.stderr.write('end %s\n' % name)

def generate_final(names, unopt_prefix, opt_prefix, both_prefix):
  info = [[]]
  for i in xrange(len(names)):
    unopt_path = TEMP_DIR + '/' + unopt_prefix + names[i] + '.txt'
    opt_path = TEMP_DIR + '/' + opt_prefix + names[i] + '.txt'
    both_path = TEMP_DIR + '/' + both_prefix + names[i] + '.txt'
    if not os.path.exists(unopt_path) or not os.path.exists(opt_path):
      # at least one is missing
      if not os.path.exists(unopt_path):
        sys.stderr.write('Unoptimized %s results missing (%s)\n' % (names[i], unopt_path))
      if not os.path.exists(opt_path):
        sys.stderr.write('Optimized %s results missing (%s)\n' % (names[i], opt_path))
      continue

    subprocess.check_call([PYTHON, COMBINE_MSCC_PATH, unopt_path, opt_path], stdout=open(both_path, 'w'))
    info.append([names[i]] + open(both_path).read().strip().split(' | '))

  header = ['bench', 'num loads/stores']
  for opt in OPTIMIZATIONS:
    header.append('num optimized by ' + opt)
  header.extend(['num optimized total', 'run-time checks before opt', 'run-time checks avoided'])
  info[0] = header

  lengths = []
  for i in xrange(len(info[0])):
    longest = 0
    for j in xrange(len(info)):
      longest = max(longest, len(info[j][i]))
    lengths.append(longest)

  for line in info:
    for i in xrange(len(line)):
      field = line[i].ljust(lengths[i], ' ')
      if i == 0:
        sys.stdout.write(field)
      elif i == len(line) - 1:
        sys.stdout.write(' | %s\n' % field.strip())
      else:
        sys.stdout.write(' | %s' % field)

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
  parser = OptionParser(usage="usage: %prog [options] SPEC_PATH CLANG_BIN_DIR")
  parser.add_option("-O", "--opt", action="store_true", dest="opt", default=False,
                    help="Using optimizing build")
  parser.add_option("-i", "--ignore-old", action="store_false", dest="use_old", default=True,
                    help="Ignore old result files")
  parser.add_option("-c", "--no-execute", action="store_false", dest="execute", default=True,
                    help="Just compile without executing")
  parser.add_option("-f", "--final", action="store_true", dest="final", default=False,
                    help="Generate final output")
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                    help="Show verbose output")
  (options, args) = parser.parse_args()
  prefix = 'opt-' if options.opt else 'unopt-'
  spec_path = args[0]
  clang_bin_dir = args[1]

  names = find_spec_names(spec_path)
  #names = ['401.bzip2', '429.mcf', '433.milc', '456.hmmer', '458.sjeng', '462.libquantum', '470.lbm']
  #names = ['470.lbm', '462.libquantum']
  #names = ['470.lbm']

  action = 'Compiling' if not options.execute else 'Compiling and running'
  sys.stderr.write('%s the following:\n' % action)
  for name in names:
    sys.stderr.write('%s\n' % name)
  sys.stderr.write('\n')

  if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

  handles = []
  Q = multiprocessing.Queue()
  for i in xrange(len(names)):
    p = WorkerProcess(names[i], Q, options.execute, TEMP_DIR + '/' + prefix, options.use_old, spec_path, clang_bin_dir)
    handles.append(p)

  pos = 0
  while pos < len(names):
    working = pos - Q.qsize()
    if working < PROCESSORS:
      handles[pos].start()
      pos += 1
    else:
      time.sleep(0.01)

  summary = ''
  for i in xrange(len(handles)):
    summary += handles[i].name + "\n" + Q.get()

  all_raw_path = TEMP_DIR + '/' + prefix + 'all-raw.txt'
  file = open(all_raw_path, 'w')
  file.write(summary)
  file.close()

  clean_out = subprocess.check_output([PYTHON, COMBINE_MSCC_PATH], stdin = open(all_raw_path))
  file = open(TEMP_DIR + '/' + prefix + 'all.txt', 'w')
  file.write(clean_out)
  file.close()

  if options.verbose:
    sys.stdout.write(clean_out)

  if options.final:
    generate_final(names + ['all'], 'unopt-', 'opt-', 'final-')
