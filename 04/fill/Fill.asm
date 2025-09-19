// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Fill.asm

// Runs an infinite loop that listens to the keyboard input. 
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel. When no key is pressed, 
// the screen should be cleared.

// Define screen end which is SCREEN + 8191 (256 rows * 32 words - 1)
@8191
D=A
@SCREEN
D=D+A
@screen_end
M=D
// Define the screen pos to be written
@SCREEN
D=A
@screen_pos
M=D
(READ_KBD)
    @KBD
    D=M
    @WHITEN
    D;JEQ
    @BLACKEN
    0;JMP
(WHITEN)
    // Write a word at pos
    @screen_pos
    A=M
    M=0
    // If pos <= SCREEN, do nothing
    @screen_pos
    D=M
    @SCREEN
    D=D-A
    @READ_KBD
    D;JLE
    // Or decrement the pos
    @screen_pos
    M=M-1
    @READ_KBD
    0;JMP
(BLACKEN)
    // Write a word at pos
    @screen_pos
    A=M
    M=-1
    // If pos >= screen end, do nothing
    @screen_pos
    D=M
    @screen_end
    D=D-M
    @READ_KBD
    D;JGE
    // Or increment the pos
    @screen_pos
    M=M+1
    @READ_KBD
    0;JMP