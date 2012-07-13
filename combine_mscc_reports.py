import re
import sys

class Summary:
  def __init__(self, title = None):
    self.title = title
    self.load_checks = 0
    self.store_checks = 0
    self.fast_load_checks = 0
    self.fast_store_checks = 0
    self.fast_load_failure_calls = 0
    self.fast_store_failure_calls = 0

  def get_total(self):
    return self.load_checks + self.store_checks + self.fast_load_checks \
         + self.fast_store_checks + self.fast_load_failure_calls \
         + self.fast_store_failure_calls

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
    return delta

  def print_report(self, reference_total = None):
    sys.stdout.write("Load/Store Check Counter report")
    if self.title is not None:
      sys.stdout.write(" (" + self.title + ")")

    total = self.get_total()
    sys.stdout.write(": %d checks\n" % total)
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

    sys.stdout.write("\n")

initial = Summary("initial")
final = Summary("final")

report_prefix = "Load/Store Check Counter report"

current_summary = None
while True:
  line = sys.stdin.readline()
  if not line:
    break

  if line.startswith(report_prefix):
    line = line[len(report_prefix):].strip()
    match = re.match("^\\((initial|final)\\): [0-9]+ checks", line)
    if not match:
      current_summary = None
    elif match.group(1) == "initial":
      current_summary = initial
    else:
      current_summary = final
    continue
  elif not current_summary:
    continue

  match = re.match("^([0-9]+) (generic|fast) (load|store) (checks|failure calls)$",
                   line.strip())
  if not match:
    continue

  amount = int(match.group(1))
  if match.group(4) == "failure calls":
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

initial.print_report()
final.print_report()
initial.get_delta(final, "optimized away").print_report(initial.get_total())
