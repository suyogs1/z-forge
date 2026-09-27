      *================================================================
      * ERRCODE.CPY — error code constants
      * ZENITH BANK (fictional) — synthetic data only
      *================================================================
       01  ERROR-CODES.
           05  ERR-NONE                PIC S9(4) COMP VALUE +0.
           05  ERR-RECORD-NOT-FOUND    PIC S9(4) COMP VALUE +4.
           05  ERR-DUPLICATE-KEY       PIC S9(4) COMP VALUE +8.
           05  ERR-IO-ERROR            PIC S9(4) COMP VALUE +12.
           05  ERR-INVALID-STATUS      PIC S9(4) COMP VALUE +16.
           05  ERR-FIELD-OVERFLOW      PIC S9(4) COMP VALUE +20.
           05  ERR-PROGRAM-ABEND       PIC S9(4) COMP VALUE +99.

       01  RETURN-CODE-WS              PIC S9(4) COMP VALUE +0.
