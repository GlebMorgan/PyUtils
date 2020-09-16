@echo off

if "%1" == "bits" set target=bits_test.py

python -m pytest tests\%target% -x --ff --no-header --no-summary %2 %3 %4 %5 %6