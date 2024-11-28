# SMTP Tester

## Intro

It is suprise to me all available STMP tester are either online or opensource but barely works. To make my life easier, I made one from scratch, based on PySide6 and other Python built-in modules.

## How to run

```shell
# prepare venv
python -m venv .venv
# activate venv
source .venv/bin/activate.sh # Linux
.venv/Scripts/activate # Windows
# get dependencies
pip install -r requirements.txt
# run the GUI
python ./main.py
```