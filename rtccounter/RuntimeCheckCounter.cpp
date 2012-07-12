#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>

namespace {
  long long LoadChecks, StoreChecks;
  long long FastLoadChecks, FastStoreChecks;
  long long FastLoadCheckFailureCalls, FastStoreCheckFailureCalls;

  void printLoadStoreSummary(FILE *F) {
    long long Total = LoadChecks + StoreChecks + FastLoadChecks
                    + FastStoreChecks + FastLoadCheckFailureCalls
                    + FastStoreCheckFailureCalls;

    fprintf(F, "====== Runtime Load/Store Check Counter Report ======\n");
    fprintf(F, "  %lld load/store checks called in total\n", Total);
    fprintf(F, "  %lld load checks called\n", LoadChecks);
    fprintf(F, "  %lld store checks called\n", StoreChecks);
    fprintf(F, "  %lld fast load checks called\n", FastLoadChecks);
    fprintf(F, "  %lld fast store checks called\n", FastStoreChecks);
    fprintf(F, "  %lld fast load check failures reported\n",
            FastLoadCheckFailureCalls);
    fprintf(F, "  %lld fast store check failures reported\n",
            FastStoreCheckFailureCalls);
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
    ++FastLoadCheckFailureCalls;
    exit(1);
  }

  void __fail_faststorecheck(void *ptr, size_t size, void *obj, size_t obj_size) {
    ++FastStoreCheckFailureCalls;
    exit(1);
  }
}
