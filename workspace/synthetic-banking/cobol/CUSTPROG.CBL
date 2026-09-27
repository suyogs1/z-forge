      *================================================================
      * CUSTPROG.CBL — Customer Maintenance Program
      * ZENITH BANK (fictional) — synthetic data only
      *
      * Reads and writes CUST.MASTER.FILE.
      * COPIES CUSTMAST — dependency: CUSTMAST → CUSTPROG.
      * Change scenario: when CUSTOMER-ID expands 8→12, this program's
      *   WORKING-STORAGE (via copybook) and SELECT/FD must be updated.
      *================================================================
       IDENTIFICATION DIVISION.
       PROGRAM-ID. CUSTPROG.
       AUTHOR. ZENITH-BANK-SYNTHETIC.
       DATE-WRITTEN. 2024-01-01.

       ENVIRONMENT DIVISION.
       CONFIGURATION SECTION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CUSTOMER-FILE ASSIGN TO CUSTMAST
               ORGANIZATION IS SEQUENTIAL
               ACCESS MODE IS SEQUENTIAL
               FILE STATUS IS WS-FILE-STATUS.

       DATA DIVISION.
       FILE SECTION.
       FD  CUSTOMER-FILE
           RECORDING MODE IS F
           BLOCK CONTAINS 0 RECORDS
           RECORD CONTAINS 80 CHARACTERS.
           COPY CUSTMAST.

       WORKING-STORAGE SECTION.
           COPY ERRCODE.

       01  WS-FILE-STATUS              PIC XX VALUE SPACES.
           88  WS-FILE-OK              VALUE '00'.
           88  WS-FILE-EOF             VALUE '10'.

       01  WS-OPERATION                PIC X VALUE SPACE.
           88  WS-OP-READ              VALUE 'R'.
           88  WS-OP-WRITE             VALUE 'W'.
           88  WS-OP-UPDATE            VALUE 'U'.

       01  WS-RECORD-COUNT             PIC 9(6) VALUE ZEROS.
       01  WS-SEARCH-ID                PIC X(8) VALUE SPACES.

       PROCEDURE DIVISION.
       0000-MAIN.
           PERFORM 1000-OPEN-FILES
           PERFORM 2000-PROCESS-RECORDS
               UNTIL WS-FILE-EOF
           PERFORM 9000-CLOSE-FILES
           STOP RUN.

       1000-OPEN-FILES.
           OPEN INPUT CUSTOMER-FILE
           IF NOT WS-FILE-OK
               MOVE ERR-IO-ERROR TO RETURN-CODE-WS
               DISPLAY 'CUSTPROG: FILE OPEN ERROR ' WS-FILE-STATUS
               STOP RUN
           END-IF.

       2000-PROCESS-RECORDS.
           READ CUSTOMER-FILE INTO CUSTOMER-MASTER-RECORD
               AT END SET WS-FILE-EOF TO TRUE
               NOT AT END
                   PERFORM 2100-VALIDATE-RECORD
                   ADD 1 TO WS-RECORD-COUNT
           END-READ.

       2100-VALIDATE-RECORD.
           IF CUSTOMER-ID = SPACES
               MOVE ERR-INVALID-STATUS TO RETURN-CODE-WS
               DISPLAY 'CUSTPROG: BLANK CUSTOMER-ID AT '
                       WS-RECORD-COUNT
           END-IF
           IF NOT (CUST-ACTIVE OR CUST-INACTIVE OR CUST-SUSPENDED)
               DISPLAY 'CUSTPROG: INVALID STATUS FOR ' CUSTOMER-ID
           END-IF.

       9000-CLOSE-FILES.
           CLOSE CUSTOMER-FILE
           DISPLAY 'CUSTPROG: PROCESSED ' WS-RECORD-COUNT ' RECORDS'.
