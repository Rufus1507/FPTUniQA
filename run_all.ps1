# PowerShell script to run entire FPTUniQA project
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONPATH = "src;."
python run_all.py $args
