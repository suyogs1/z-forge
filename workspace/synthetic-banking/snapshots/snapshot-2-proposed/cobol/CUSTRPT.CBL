      *================================================================
      * CUSTRPT.CBL — Customer Report Generator
      * ZENITH BANK (fictional) — synthetic data only
      *
      * Reads CUST.MASTER.FILE, writes CUST.REPORT.FILE.
      * COPIES CUSTMAST — dependency: CUSTMAST → CUSTRPT.
      * MOVEs CUSTOMER-ID to output — offset-sensitive.
      * Change scenario: when CUSTOMER-ID expands 8→12, the MOVE
      *   statements and report layout must be updated.
      * Data lineage: CUST.MASTER.FILE → CUSTRPT → CUST.REPORT.FILE
      *   → AFP output (CUSTRPT.AFP)
      *================================================================
       IDENTIFICATION DIVISION.
       PROGRAM-ID. CUSTRPT.
       AUTHOR. ZENITH-BANK-SYNTHETIC.
       DATE-WRITTEN. 2024-01-01.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT CUSTOMER-FILE ASSIGN TO CUSTMAST
               ORGANIZATION IS SEQUENTIAL
               ACCESS MODE IS SEQUENTIAL
               FILE STATUS IS WS-IN-STATUS.
           SELECT REPORT-FILE ASSIGN TO CUSTRPT
               ORGANIZATION IS SEQUENTIAL
               ACCESS MODE IS SEQUENTIAL
               FILE STATUS IS WS-OUT-STATUS.

       DATA DIVISION.
       FILE SECTION.
       FD  CUSTOMER-FILE
           RECORDING MODE IS F
           RECORD CONTAINS 80 CHARACTERS.
           COPY CUSTMAST.

       FD  REPORT-FILE
           RECORDING MODE IS F
           RECORD CONTAINS 133 CHARACTERS.
       01  REPORT-RECORD               PIC X(133).

       WORKING-STORAGE SECTION.
           COPY ERRCODE.

       01  WS-IN-STATUS                PIC XX VALUE SPACES.
           88  WS-IN-OK                VALUE '00'.
           88  WS-IN-EOF               VALUE '10'.
       01  WS-OUT-STATUS               PIC XX VALUE SPACES.
           88  WS-OUT-OK               VALUE '00'.

       01  WS-REPORT-LINE.
           05  RPT-LINE-TYPE           PIC X.
           05  RPT-CUSTOMER-ID         PIC X(8).
           05  FILLER                  PIC X VALUE SPACE.
           05  RPT-CUSTOMER-NAME       PIC X(30).
           05  FILLER                  PIC X VALUE SPACE.
           05  RPT-STATUS              PIC X.
           05  FILLER                  PIC X VALUE SPACE.
           05  RPT-OPEN-DATE           PIC X(8).
           05  FILLER                  PIC X(82).

       01  WS-RECORD-COUNT             PIC 9(6) VALUE ZEROS.
       01  WS-ACTIVE-COUNT             PIC 9(6) VALUE ZEROS.

       PROCEDURE DIVISION.
       0000-MAIN.
           PERFORM 1000-OPEN-FILES
           PERFORM 2000-WRITE-HEADER
           PERFORM 3000-PROCESS-RECORDS
               UNTIL WS-IN-EOF
           PERFORM 4000-WRITE-SUMMARY
           PERFORM 9000-CLOSE-FILES
           STOP RUN.

       1000-OPEN-FILES.
           OPEN INPUT CUSTOMER-FILE
           OPEN OUTPUT REPORT-FILE
           IF NOT WS-IN-OK
               DISPLAY 'CUSTRPT: INPUT FILE OPEN ERROR'
               STOP RUN
           END-IF.

       2000-WRITE-HEADER.
           MOVE SPACES TO REPORT-RECORD
           MOVE 'H' TO REPORT-RECORD(1:1)
           MOVE 'ZENITH BANK - CUSTOMER MASTER REPORT' TO
               REPORT-RECORD(3:36)
           WRITE REPORT-RECORD.

       3000-PROCESS-RECORDS.
           READ CUSTOMER-FILE INTO CUSTOMER-MASTER-RECORD
               AT END SET WS-IN-EOF TO TRUE
               NOT AT END
                   PERFORM 3100-WRITE-DETAIL-LINE
                   ADD 1 TO WS-RECORD-COUNT
                   IF CUST-ACTIVE
                       ADD 1 TO WS-ACTIVE-COUNT
                   END-IF
           END-READ.

       3100-WRITE-DETAIL-LINE.
           MOVE 'D'           TO RPT-LINE-TYPE
           MOVE CUSTOMER-ID   TO RPT-CUSTOMER-ID
           MOVE CUSTOMER-NAME TO RPT-CUSTOMER-NAME
           MOVE CUSTOMER-STATUS TO RPT-STATUS
           MOVE CUSTOMER-OPEN-DATE TO RPT-OPEN-DATE
           WRITE REPORT-RECORD FROM WS-REPORT-LINE.

       4000-WRITE-SUMMARY.
           MOVE SPACES TO REPORT-RECORD
           MOVE 'T' TO REPORT-RECORD(1:1)
           MOVE WS-RECORD-COUNT TO REPORT-RECORD(3:6)
           MOVE WS-ACTIVE-COUNT TO REPORT-RECORD(10:6)
           WRITE REPORT-RECORD.

       9000-CLOSE-FILES.
           CLOSE CUSTOMER-FILE
           CLOSE REPORT-FILE
           DISPLAY 'CUSTRPT: REPORT WRITTEN ' WS-RECORD-COUNT
                   ' RECORDS, ' WS-ACTIVE-COUNT ' ACTIVE'.
