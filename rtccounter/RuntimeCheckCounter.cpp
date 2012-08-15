#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

namespace {
  long long LoadChecks, StoreChecks;
  long long FastLoadChecks, FastStoreChecks;
  long long FastLoadFailures, FastStoreFailures;
  long long GlobalRegistrations, StackRegistrations;

  void printSummary(FILE *F) {
    long long GenericChecks = LoadChecks + StoreChecks;
    long long FastChecks = FastLoadChecks + FastStoreChecks;
    long long FastFailureCalls = FastLoadFailures + FastStoreFailures;
    long long MemoryRegistrations = GlobalRegistrations + StackRegistrations;
    long long Sum = GenericChecks + FastChecks + FastFailureCalls
                  + MemoryRegistrations;

    fprintf(F, "Runtime Memory Safety Call Counter report: %lld calls\n",
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

    fprintf(F, "%lld memory registration calls (%d%%)\n",
            MemoryRegistrations, int(100 * MemoryRegistrations / Sum));
    if (MemoryRegistrations) {
      fprintf(F, "  %lld global registration calls\n",
              GlobalRegistrations);
      fprintf(F, "  %lld stack registration calls\n",
              StackRegistrations);
    }

    fprintf(F, "\n");
  }

  void printReport() {
    if (const char *path = getenv("RTCC_PATH")) {
      FILE *F = fopen(path, "w");
      printSummary(F);
      fclose(F);
    } else {
      printSummary(stderr);
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

  void __pool_register_global(void *ptr, size_t size) {
    ++GlobalRegistrations;
  }

  void __pool_register_stack(void *ptr, size_t size) {
    ++StackRegistrations;
  }

  void __pool_unregister_stack(void *ptr) {
    // ignore for now
  }
}
