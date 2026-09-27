      *================================================================
      * ACCTMAST.CPY — ACCOUNT-MASTER-RECORD copybook
      * ZENITH BANK (fictional) — synthetic data only
      *
      * This copybook includes CUSTMAST, establishing a copybook chain:
      *   CUSTMAST → ACCTMAST → ACCTPROG
      * Any change to CUSTMAST.CPY propagates through this copybook.
      *================================================================
       01  ACCOUNT-MASTER-RECORD.
           05  ACCOUNT-NUMBER          PIC X(10).
           05  ACCOUNT-TYPE            PIC X.
               88  ACCT-CHECKING       VALUE 'C'.
               88  ACCT-SAVINGS        VALUE 'S'.
               88  ACCT-LOAN           VALUE 'L'.
           05  ACCOUNT-BALANCE         PIC S9(11)V99 COMP-3.
           05  ACCOUNT-OPEN-DATE       PIC X(8).
           05  ACCOUNT-LAST-TXN-DATE   PIC X(8).
           05  ACCOUNT-STATUS          PIC X.
               88  ACCT-ACTIVE         VALUE 'A'.
               88  ACCT-CLOSED         VALUE 'C'.
           05  ACCOUNT-OWNER-RECORD.
               COPY CUSTMAST.
