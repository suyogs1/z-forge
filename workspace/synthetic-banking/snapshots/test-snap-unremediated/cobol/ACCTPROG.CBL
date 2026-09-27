      *================================================================
      * ACCTPROG.CBL — Account Processing Program
      * ZENITH BANK (fictional) — synthetic data only
      *
      * COPIES ACCTMAST (which in turn COPIES CUSTMAST).
      * Dependency chain: CUSTMAST → ACCTMAST → ACCTPROG.
      * CALLS CUSTPROG for customer validation.
      *
      * *** PLANTED FAILURE — DO NOT FIX UNTIL T6 ADVERSARIAL PASS ***
      *
      * WS-ACCT-CUST-ID is declared locally in WORKING-STORAGE as
      * PIC X(8). It is NOT sourced from any copybook.
      * After CUSTMAST.CPY is updated to CUSTOMER-ID PIC X(12),
      * the MOVE CUSTOMER-ID TO WS-ACCT-CUST-ID will write 12 bytes
      * into an 8-byte field — data truncation.
      *
      * The actor (LocalSyntaxAdapter) does NOT catch this because
      * the syntax is valid. The adversarial critic and the
      * DeterministicScenarioAdapter ARE required to surface this.
      *================================================================
       IDENTIFICATION DIVISION.
       PROGRAM-ID. ACCTPROG.
       AUTHOR. ZENITH-BANK-SYNTHETIC.
       DATE-WRITTEN. 2024-01-01.

       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT ACCOUNT-FILE ASSIGN TO ACCTMAST
               ORGANIZATION IS SEQUENTIAL
               ACCESS MODE IS SEQUENTIAL
               FILE STATUS IS WS-FILE-STATUS.

       DATA DIVISION.
       FILE SECTION.
       FD  ACCOUNT-FILE
           RECORDING MODE IS F
           RECORD CONTAINS 80 CHARACTERS.
           COPY ACCTMAST.

       WORKING-STORAGE SECTION.
           COPY ERRCODE.

       01  WS-FILE-STATUS              PIC XX VALUE SPACES.
           88  WS-FILE-OK              VALUE '00'.
           88  WS-FILE-EOF             VALUE '10'.

      *----------------------------------------------------------------
      * PLANTED FAILURE: WS-ACCT-CUST-ID is PIC X(8) — local
      * declaration, NOT sourced from CUSTMAST copybook.
      * When CUSTOMER-ID expands to PIC X(12), this field stays at
      * PIC X(8) unless explicitly updated.
      * The MOVE statement below will silently truncate 4 bytes.
      *----------------------------------------------------------------
       01  WS-ACCT-CUST-ID             PIC X(8).
       01  WS-ACCT-BALANCE-WORK        PIC S9(13)V99 COMP-3.
       01  WS-PROCESS-COUNT            PIC 9(6) VALUE ZEROS.
       01  WS-ERROR-COUNT              PIC 9(6) VALUE ZEROS.

       PROCEDURE DIVISION.
       0000-MAIN.
           PERFORM 1000-OPEN-FILES
           PERFORM 2000-PROCESS-ACCOUNTS
               UNTIL WS-FILE-EOF
           PERFORM 9000-CLOSE-FILES
           STOP RUN.

       1000-OPEN-FILES.
           OPEN INPUT ACCOUNT-FILE
           IF NOT WS-FILE-OK
               MOVE ERR-IO-ERROR TO RETURN-CODE-WS
               DISPLAY 'ACCTPROG: FILE OPEN ERROR ' WS-FILE-STATUS
               STOP RUN
           END-IF.

       2000-PROCESS-ACCOUNTS.
           READ ACCOUNT-FILE INTO ACCOUNT-MASTER-RECORD
               AT END SET WS-FILE-EOF TO TRUE
               NOT AT END
                   PERFORM 2100-VALIDATE-ACCOUNT
                   ADD 1 TO WS-PROCESS-COUNT
           END-READ.

       2100-VALIDATE-ACCOUNT.
      *----------------------------------------------------------------
      * PLANTED FAILURE: MOVE CUSTOMER-ID TO WS-ACCT-CUST-ID
      * After expansion, CUSTOMER-ID is PIC X(12) but
      * WS-ACCT-CUST-ID remains PIC X(8) → truncation of 4 bytes.
      *----------------------------------------------------------------
           MOVE CUSTOMER-ID TO WS-ACCT-CUST-ID
           IF WS-ACCT-CUST-ID = SPACES
               ADD 1 TO WS-ERROR-COUNT
               DISPLAY 'ACCTPROG: BLANK CUSTOMER-ID IN ACCOUNT '
                       ACCOUNT-NUMBER
           END-IF
           IF ACCT-ACTIVE
               PERFORM 2200-PROCESS-ACTIVE-ACCOUNT
           END-IF.

       2200-PROCESS-ACTIVE-ACCOUNT.
           CALL 'CUSTPROG' USING ACCOUNT-MASTER-RECORD
               ON EXCEPTION
                   ADD 1 TO WS-ERROR-COUNT
                   DISPLAY 'ACCTPROG: CUSTPROG CALL FAILED FOR '
                           WS-ACCT-CUST-ID
           END-CALL.

       9000-CLOSE-FILES.
           CLOSE ACCOUNT-FILE
           DISPLAY 'ACCTPROG: PROCESSED ' WS-PROCESS-COUNT
                   ' ACCOUNTS, ' WS-ERROR-COUNT ' ERRORS'.
