import re
import sys

report_prefix = "Memory Safety Call Counter report"
runtime_report_prefix = "Runtime Memory Safety Call Counter report"

class Summary:
  def __init__(self, title = None):
    self.title = title
    self.load_checks = 0
    self.store_checks = 0
    self.fast_load_checks = 0
    self.fast_store_checks = 0
    self.fast_load_failure_calls = 0
    self.fast_store_failure_calls = 0
    self.global_registrations = 0
    self.stack_registrations = 0

  def get_total_ls_checks(self):
    return self.load_checks + self.store_checks + self.fast_load_checks \
         + self.fast_store_checks + self.fast_load_failure_calls \
         + self.fast_store_failure_calls

  def get_total_registrations(self):
    return self.global_registrations + self.stack_registrations

  def get_total(self):
    return self.get_total_ls_checks() + self.get_total_registrations()

  def get_delta(self, other, title = None):
    delta = Summary(title)
    delta.load_checks = self.load_checks - other.load_checks
    delta.store_checks = self.store_checks - other.store_checks
    delta.fast_load_checks = self.fast_load_checks - other.fast_load_checks
    delta.fast_store_checks = self.fast_store_checks - other.fast_store_checks
    delta.fast_load_failure_calls = self.fast_load_failure_calls \
                                  - other.fast_load_failure_calls
    delta.fast_store_failure_calls = self.fast_store_failure_calls \
                                   - other.fast_store_failure_calls
    delta.global_registrations = self.global_registrations \
                               - other.global_registrations
    delta.stack_registrations = self.stack_registrations \
                              - other.stack_registrations
    return delta

  def print_report(self, reference_total = None):
    sys.stdout.write(report_prefix if self.title != 'runtime' else runtime_report_prefix)
    if self.title is not None and self.title != 'runtime':
      sys.stdout.write(" (" + self.title + ")")

    total = self.get_total()
    sys.stdout.write(": %d calls\n" % total)
    if not total:
      return

    reference_total = total if reference_total is None else reference_total
    generic_checks = self.load_checks + self.store_checks
    sys.stdout.write("%d generic load/store checks (%d%%)\n" %
                    (generic_checks, 100 * generic_checks / reference_total if reference_total else 0))
    if generic_checks:
      sys.stdout.write("  %d generic load checks\n" % self.load_checks)
      sys.stdout.write("  %d generic store checks\n" % self.store_checks)

    fast_checks = self.fast_load_checks + self.fast_store_checks
    sys.stdout.write("%d fast load/store checks (%d%%)\n" %
                     (fast_checks, 100 * fast_checks / reference_total if reference_total else 0))
    if fast_checks:
      sys.stdout.write("  %d fast load checks\n" % self.fast_load_checks)
      sys.stdout.write("  %d fast store checks\n" % self.fast_store_checks)

    fast_failure_calls = self.fast_load_failure_calls \
                       + self.fast_store_failure_calls
    sys.stdout.write("%d fast load/store failure calls (%d%%)\n" %
                     (fast_failure_calls, 100 * fast_failure_calls / reference_total if reference_total else 0))
    if fast_failure_calls:
      sys.stdout.write("  %d fast load failure calls\n" %
                       self.fast_load_failure_calls)
      sys.stdout.write("  %d fast store failure calls\n" %
                       self.fast_store_failure_calls)
    
    registration_calls = self.global_registrations + self.stack_registrations
    sys.stdout.write("%d memory registration calls (%d%%)\n" %
                     (registration_calls, 100 * registration_calls / reference_total if reference_total else 0))
    if registration_calls:
      sys.stdout.write("  %d global registration calls\n" %
                       self.global_registrations)
      sys.stdout.write("  %d stack registration calls\n" %
                       self.stack_registrations)

    sys.stdout.write("\n")

class MiniSummary:
  def __init__(self, code_initial, opt_progress, runtime_initial, runtime_final):
    self.code_initial = code_initial
    self.opt_progress = opt_progress
    self.runtime_initial = runtime_initial
    self.runtime_final = runtime_final
    self.keys = sorted(opt_progress.keys())

  def format_number(self, number, max_len):
    s = str(int(number))
    res = ''
    for i in xrange(len(s)):
      if (len(s) - i) % 3 == 0 and i != 0:
        res += ','
      res += s[i]
    return res.rjust(max_len, ' ')

  def print_report(self):
    # initial checks
    initial_number = self.code_initial.get_total_ls_checks()
    last_number = initial_number
    sys.stdout.write('%d' % initial_number)

    # optimized by various individual optimizations
    optimized_total = 0
    for key in self.keys:
      optimized_here = last_number - self.opt_progress[key].get_total_ls_checks()
      optimized_total += optimized_here
      last_number = self.opt_progress[key].get_total_ls_checks()
      percent = 0.0 if initial_number == 0 else 100.0 * optimized_here / initial_number
      sys.stdout.write(' | %d (%.0f%%)' % (optimized_here, percent))

    # optimized in total
    optimized_total_percent = 0.0 if initial_number == 0 else 100.0 * optimized_total / initial_number
    sys.stdout.write(' | %d (%.0f%%)' % (optimized_total, optimized_total_percent))

    # runtime checks before optimizations
    runtime_initial = self.runtime_initial.get_total_ls_checks()
    sys.stdout.write(' | %d' % runtime_initial)

    # runtime checks avoided
    runtime_avoided = runtime_initial - self.runtime_final.get_total_ls_checks()
    runtime_avoided_percent = 0.0 if runtime_initial == 0 else 100.0 * runtime_avoided / runtime_initial
    sys.stdout.write(' | %d (%.0f%%)' % (runtime_avoided, runtime_avoided_percent))
    sys.stdout.write('\n')

class Parser:
  def __init__(self, stream):
    self.stream = stream
    self.initial = Summary("initial")
    self.final = Summary("final")
    self.final_lto = Summary("final-lto")
    self.runtime = Summary("runtime")
    self.opt_progress = {}
    self.parse()

  def parse(self):
    current_summary = None
    while True:
      line = self.stream.readline()
      if not line:
        break

      if line.startswith(report_prefix):
        line = line[len(report_prefix):].strip()
        match = re.match("^\\((initial|final|final-lto|opt_progress_[0-9]+)\\): [0-9]+ calls", line)
        if not match:
          current_summary = None
        elif match.group(1) == "initial":
          current_summary = self.initial
        elif match.group(1) == "final":
          current_summary = self.final
        elif match.group(1).startswith("opt_progress_"):
          num = int(match.group(1)[len("opt_progress_")])
          if num not in self.opt_progress:
            self.opt_progress[num] = Summary(match.group(1))
          current_summary = self.opt_progress[num]
        else:
          current_summary = self.final_lto
        continue
      elif line.startswith(runtime_report_prefix):
        current_summary = self.runtime
      elif not current_summary:
        continue

      match = re.match("^([0-9]+) (global|stack) registration calls$", line.strip())
      if match:
        amount = int(match.group(1))
        if match.group(2) == "global":
          current_summary.global_registrations += amount
        else:
          current_summary.stack_registrations += amount
        continue

      match = re.match("^([0-9]+) (generic|fast) (load|store) (checks|failure calls|check failures reported)$",
                      line.strip())
      if not match:
        continue

      amount = int(match.group(1))
      if match.group(4) == "check failures reported" or match.group(4) == "failure calls":
        if match.group(3) == "load":
          current_summary.fast_load_failure_calls += amount
        else:
          current_summary.fast_store_failure_calls += amount
      elif match.group(2) == "generic":
        if match.group(3) == "load":
          current_summary.load_checks += amount
        else:
          current_summary.store_checks += amount
      else:
        if match.group(3) == "load":
          current_summary.fast_load_checks += amount
        else:
          current_summary.fast_store_checks += amount

  def print_report(self):
    for num, data in self.opt_progress.iteritems():
      data.print_report()

    last = self.final_lto if self.final_lto.get_total() else self.final

    if self.initial.get_total():
      self.initial.print_report()
      self.final.print_report()
      if self.final_lto.get_total():
        self.final_lto.print_report()

      self.initial.get_delta(last, "optimized away").print_report(self.initial.get_total())

    if self.runtime.get_total():
      # hack to estimate the number of global registrations
      self.runtime.global_registrations = last.global_registrations

      self.runtime.print_report()

if len(sys.argv) == 3:
  # mini summary based on 2 files: unoptimized runtime, optimized runtime
  unoptimized = Parser(open(sys.argv[1]))
  optimized = Parser(open(sys.argv[2]))
  summary = MiniSummary(unoptimized.initial, optimized.opt_progress, unoptimized.runtime, optimized.runtime)
  summary.print_report()
else:
  # read from stdin
  parser = Parser(sys.stdin)
  parser.print_report()
