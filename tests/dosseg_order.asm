; DOSSEG keeps DGROUP classes between BEGDATA and BSS/STACK in first-seen
; order. BASIC holds BC_DATA..BC_FT as one range; reordered, it is negative.
    .dosseg
DGROUP group _DATA, BC_DATA, BC_VARS, BC_FT, BC_CN
_DATA segment word public 'DATA'
    db 'RANGE:'
    dw offset DGROUP:rstart, offset DGROUP:rend
_DATA ends
BC_DATA segment word public 'BC_DATA'
rstart dw ?
BC_DATA ends
BC_VARS segment word public 'BC_VARS'
    dw 1
BC_VARS ends
BC_FT segment word public 'BC_SEGS'
rend label word
BC_FT ends
BC_CN segment word public 'BC_SEGS'
    dw 2
BC_CN ends
_TEXT segment word public 'CODE'
    assume cs:_TEXT, ds:DGROUP
start:
    mov ax, 4c00h
    int 21h
_TEXT ends
STACK segment para stack 'STACK'
    db 128 dup(?)
STACK ends
end start
