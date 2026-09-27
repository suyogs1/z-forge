***********************************************************************
* CUSTDSCT.ASM — Customer Master Record DSECT
* ZENITH BANK (fictional) — synthetic data only
*
* This DSECT mirrors the CUSTMAST copybook layout for use in batch
* performance modules written in HLASM. CUSTID DS CL8 must stay
* synchronized with CUSTMAST.CPY CUSTOMER-ID PIC X(8).
*
* Dependency: CUSTMAST → CUSTDSCT (layout mirror, not a COPY link)
* Change scenario: when CUSTOMER-ID expands 8→12, CUSTID DS CL8
*   must become DS CL12 and all downstream EQU offsets must shift.
***********************************************************************
CUSTMREC DSECT
*
* ---- Customer Identification ----------------------------------------
*
CUSTID   DS    CL12             Customer ID (mirrors CUSTOMER-ID PIC X(8))
CUSTNAME DS    CL30            Customer name
CUSTADR1 DS    CL30            Address line 1
CUSTADR2 DS    CL20            Address line 2
CUSTCITY DS    CL15            City
CUSTST   DS    CL2             State code
CUSTZIP  DS    CL10            ZIP/postal code
CUSTSTUS DS    CL1             Status: A=Active, I=Inactive, S=Suspended
CUSTDATE DS    CL8             Account open date (YYYYMMDD)
CUSTFILL DS    CL36            Reserved / filler
*
* ---- Computed offsets (EQU) -----------------------------------------
*
CUSTLEN  EQU   *-CUSTMREC      Total DSECT length = 160 bytes
CUSTIDLN EQU   12               Length of CUSTID field
CUSTNMLN EQU   30              Length of CUSTNAME field
*
* Usage in batch module:
*   USING CUSTMREC,R4           Map record buffer to DSECT
*   L     R5,CUSTID(,R4)        Load 8-byte customer ID  (not valid LR use)
*   MVC   CUSTID(CUSTIDLN,R4),INBUFF  Move CL8 from input buffer
*
         END
