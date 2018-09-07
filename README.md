# Google Mail

uses google api to orangize my email

## Why

I sign up for accounts online using the following template: myemail+company@gmail.com.
So why not have something that takes my emails and sort them into sub-mailboxes? Thats what this does.
Now all the emails in my inbox are from real people and not companys which I used my email to sign up for.


## Poor Mans example
For example if I sign up for amazon with the address myemail+amazon@gmail.com, this script will parse that email, and put it into a directory called Accounts/amazon. Now it's out of my mailbox and in the amazon mailbox. Nice.
You can also specify what parent mailbox to put the email under. In my example my parent mailbox was "Accounts".



## Files

- core.py: main script
- utils.py: the main files


### Notes

Cleanup is needed.