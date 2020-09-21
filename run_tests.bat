@echo off

python -m pytest tests -k %1 -x -v --ff --nf --no-header %2 %3 %4 %5 %6