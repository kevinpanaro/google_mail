import utils

def core():

    PARENT = "Accounts"

    # utils.init_logging(loglevel="INFO", logdir=None, logroot=None)
    utils.move_mail(max_results=10, parent=PARENT, dry_run=False, remove_from_inbox=True)

if __name__ == '__main__':
    core()