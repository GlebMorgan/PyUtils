@echo off

if "%1" == "bits" set target=bits_test.py

python -m pytest tests\%target% -x --ff %2 %3 %4 %5 %6