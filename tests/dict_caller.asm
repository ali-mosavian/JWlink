; Calls _needed, which only a library holds.
extrn _needed:far
_TEXT segment word public 'CODE'
start:
    call _needed
    mov ax, 4c00h
    int 21h
_TEXT ends
_STACK segment para stack 'STACK'
    db 256 dup(?)
_STACK ends
end start
