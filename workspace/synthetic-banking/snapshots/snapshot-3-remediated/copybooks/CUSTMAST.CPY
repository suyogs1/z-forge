      *================================================================
      * CUSTMAST.CPY — CUSTOMER-MASTER-RECORD copybook
      * ZENITH BANK (fictional) — synthetic data only
      *
      * IMPORTANT: CUSTOMER-ID PIC X(8) is the field targeted for
      * expansion in the demo scenario (8 → 12 bytes).
      * Blast-radius analysis starts here.
      *================================================================
       01  CUSTOMER-MASTER-RECORD.
           05  CUSTOMER-ID             PIC X(12).
           05  CUSTOMER-NAME           PIC X(30).
           05  CUSTOMER-ADDRESS-1      PIC X(30).
           05  CUSTOMER-ADDRESS-2      PIC X(20).
           05  CUSTOMER-CITY           PIC X(15).
           05  CUSTOMER-STATE          PIC XX.
           05  CUSTOMER-ZIP            PIC X(10).
           05  CUSTOMER-STATUS         PIC X.
               88  CUST-ACTIVE         VALUE 'A'.
               88  CUST-INACTIVE       VALUE 'I'.
               88  CUST-SUSPENDED      VALUE 'S'.
           05  CUSTOMER-OPEN-DATE      PIC X(8).
           05  FILLER                  PIC X(36).
      *  Total: 8+30+30+20+15+2+10+1+8+36 = 160 bytes (padded to 160)
      *  Record length for CUST.MASTER.FILE is 80 bytes (first 80 used)
