; A fixup naming its frame explicitly (DGROUP:v). The linker keeps that
; frame as a host pointer; stored in 32 bits, a 64-bit jwlink crashed.
DGROUP group _DATA
_DATA segment word public 'DATA'
v   dw 1234h
_DATA ends
_TEXT segment word public 'CODE'
    assume cs:_TEXT, ds:DGROUP
start:
    mov ax, DGROUP
    mov ds, ax
    mov ax, offset DGROUP:v
    mov ax, 4c00h
    int 21h
_TEXT ends
_STACK segment para stack 'STACK'
    db 256 dup(?)
_STACK ends
end start
