#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

namespace {
  long long LoadChecks, StoreChecks;
  long long FastLoadChecks, FastStoreChecks;
  long long FastLoadFailures, FastStoreFailures;

  void printLoadStoreSummary(FILE *F) {
    long long GenericChecks = LoadChecks + StoreChecks;
    long long FastChecks = FastLoadChecks + FastStoreChecks;
    long long FastFailureCalls = FastLoadFailures + FastStoreFailures;
    long long Sum = GenericChecks + FastChecks + FastFailureCalls;

    fprintf(F, "Runtime Load/Store Check Counter report: %lld checks called\n",
            Sum);
    if (!Sum)
      return;

    fprintf(F, "%lld generic load/store checks called (%d%%)\n",
            GenericChecks, int(100 * GenericChecks / Sum));
    if (GenericChecks) {
      fprintf(F, "  %lld generic load checks\n", LoadChecks);
      fprintf(F, "  %lld generic store checks\n", StoreChecks);
    }

    fprintf(F, "%lld fast load/store checks called (%d%%)\n",
            FastChecks, int(100 * FastChecks / Sum));
    if (FastChecks) {
      fprintf(F, "  %lld fast load checks\n", FastLoadChecks);
      fprintf(F, "  %lld fast store checks\n", FastStoreChecks);
    }

    fprintf(F, "%lld fast check failures reported (%d%%)\n",
            FastFailureCalls, int(100 * FastChecks / Sum));
    if (FastFailureCalls) {
      fprintf(F, "  %lld fast load check failures reported\n",
              FastLoadFailures);
      fprintf(F, "  %lld fast store check failures reported\n",
              FastStoreFailures);
    }
  }

  void printReport() {
    if (const char *path = getenv("RTCC_PATH")) {
      FILE *F = fopen(path, "w");
      printLoadStoreSummary(F);
      fclose(F);
    } else {
      printLoadStoreSummary(stderr);
    }
  }

  struct RuntimeCheckCounter {
    ~RuntimeCheckCounter() {
      printReport();
    }
  } X;
}

extern "C" {
  void __loadcheck(void*ptr, size_t size) {
    ++LoadChecks;
  }

  void __storecheck(void *ptr, size_t size) {
    ++StoreChecks;
  }

  void __fastloadcheck(void *ptr, size_t size, void *obj, size_t obj_size) {
    ++FastLoadChecks;
  }

  void __faststorecheck(void *ptr, size_t size, void *obj, size_t obj_size) {
    ++FastStoreChecks;
  }

  void __fail_fastloadcheck(void *ptr, size_t size, void *obj, size_t obj_size) {
    ++FastLoadFailures;
    exit(1);
  }

  void __fail_faststorecheck(void *ptr, size_t size, void *obj, size_t obj_size) {
    ++FastStoreFailures;
    exit(1);
  }
}
