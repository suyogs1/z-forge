//CUSTLOAD JOB (ZENITH),
//         'CUST MASTER LOAD',
//         CLASS=A,
//         MSGCLASS=X,
//         NOTIFY=&SYSUID
//*
//* CUSTLOAD.JCL — Load Customer Master File
//* ZENITH BANK (fictional) — synthetic data only
//*
//* Loads CUST.MASTER.FILE from sequential input.
//* LRECL=80 must match the record length in CUSTMAST.CPY.
//* Change scenario: when CUSTOMER-ID expands 8→12, record length
//*   may grow and LRECL must be updated to match.
//*
//STEP010  EXEC PGM=IDCAMS
//SYSPRINT DD  SYSOUT=*
//SYSIN    DD  *
  DEFINE CLUSTER                                          -
    (NAME(ZENITH.CUST.MASTER.FILE)                       -
     CYLINDERS(1 1)                                      -
     RECORDSIZE(80 80)                                   -
     INDEXED                                             -
     KEYS(8 0)                                           -
     SHAREOPTIONS(2 3))
/*
//STEP020  EXEC PGM=CUSTPROG
//STEPLIB  DD  DSN=ZENITH.LOADLIB,DISP=SHR
//CUSTMAST DD  DSN=ZENITH.CUST.MASTER.FILE,
//             DISP=OLD
//INFILE   DD  DSN=ZENITH.CUST.INPUT.SEQ,
//             DISP=SHR,
//             DCB=(RECFM=FB,LRECL=80,BLKSIZE=3200)
//SYSOUT   DD  SYSOUT=*
//SYSPRINT DD  SYSOUT=*
