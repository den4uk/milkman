# milkman

## What is this?
This is a simple web app, its intention is to run an office milk purchasing club.
If someone purchases milk once a week (or at other intervals), an email is sent to the 'Milkman'.
Features include:
* Adding/removing/pausing/resuming participants
* Changing the intervals how often milk is purchased
* E-mailing a reminder to the 'Milkman'
* Customising an e-mail template

## Setup
1. Have a Python3.x environment (virtual or native) on your computer/server (how about a Raspberry Pi?!)
2. Get the source code:
```$ git clone https://github.com/den4uk/milkman.git```
3. Enter directory:
```$ cd milkman/```
4. Install your dependables:
```$ pip install -r requirements.txt```
5. Initialise the database for the app:
```
$ python
>>> from milk import *
>>> init_db()
>>> exit()
```
6. Run the app in a development mode:
```$ python milk.py```

## Example
Current example of the app in action: https://milk.saz.lt
