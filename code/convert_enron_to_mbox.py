#!/usr/bin/env python

import mailbox
import sys
import email
import os
import glob
import shutil
import random


def maildir2mailbox(maildirname, mboxfilename):
    global emailsindex
    global maxemails  # open the existing maildir and the target mbox file
    maildir = mailbox.Maildir(maildirname, email.message_from_file)
    mbox = mailbox.mbox(mboxfilename)

    # lock the mbox
    mbox.lock()

    # iterate over messages in the maildir and add to the mbox
    for msg in maildir:
        if emailsindex < maxemails:
            mbox.add(msg)
            emailsindex += 1
        else:
            print("wrote " + str(maxemails) + " emails")
            break

    # close and unlock
    mbox.close()
    maildir.close()


folders = []
emailsindex = 0
maxemails = 2279
outputfile = "enron-mbox"+str(maxemails)+".mbox"

# traverse root directory, and list directories as dirs and files as files
for root, dirs, files in os.walk("maildir"):
    if files:
        folders.append(root)

for folder in folders:
  print("Processing " + folder)
  os.makedirs(folder + "/cur")
  os.makedirs(folder + "/new")
  for file in glob.glob(folder + "/[0-9]*_"):
    shutil.move(file, folder + "/cur")

os.makedirs("enron")

random.shuffle(folders)
for folder in folders:
    folder = folder.replace("\\cur", "")
    # path = "enron/" + folder.replace("\\", ".").replace("maildir", "enron")
    path = "enron/" + outputfile
    if emailsindex < maxemails:
        print("Writing " + folder + " -> " + path)
        maildir2mailbox(folder, path)
