//CUSTRPT  JOB (ZENITH),
//         'CUST REPORT',
//         CLASS=A,
//         MSGCLASS=X,
//         NOTIFY=&SYSUID
//*
//* CUSTRPT.JCL — Customer Report Job
//* ZENITH BANK (fictional) — synthetic data only
//*
//* Runs CUSTRPT program.
//* Reads CUST.MASTER.FILE, writes CUST.REPORT.FILE.
//* Data lineage: CUST.MASTER.FILE → CUSTRPT.CBL → CUST.REPORT.FILE
//*                                              → CUSTRPT.AFP (output)
//*
//STEP010  EXEC PGM=CUSTRPT
//STEPLIB  DD  DSN=ZENITH.LOADLIB,DISP=SHR
//CUSTMAST DD  DSN=ZENITH.CUST.MASTER.FILE,
//             DISP=SHR,
//             DCB=(RECFM=FB,LRECL=80,BLKSIZE=3200)
//CUSTRPT  DD  DSN=ZENITH.CUST.REPORT.FILE,
//             DISP=(NEW,CATLG,DELETE),
//             UNIT=SYSDA,
//             SPACE=(CYL,(1,1)),
//             DCB=(RECFM=FBA,LRECL=133,BLKSIZE=5320)
//AFPOUT   DD  DSN=ZENITH.CUSTRPT.AFP,
//             DISP=(NEW,CATLG,DELETE),
//             UNIT=SYSDA,
//             SPACE=(CYL,(1,1))
//SYSOUT   DD  SYSOUT=*
//SYSPRINT DD  SYSOUT=*
