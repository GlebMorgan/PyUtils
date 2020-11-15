@echo off
cls
python -m pytest %1 -x -v --ff --nf --no-header %2 %3 %4 %5 %6