"""Windows-friendly passphrase launcher. No cloud credentials are requested here."""
import os
import re
from pathlib import Path
import tkinter as tk
from tkinter import simpledialog,messagebox
from core import Store
from server import serve


def main():
    window=tk.Tk();window.withdraw()
    workspace=simpledialog.askstring('Palm92 Private Analyst','Workspace label (use a separate label for each employer or charity):',initialvalue='private-1')
    if not workspace:return
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,40}',workspace):
        messagebox.showerror('Workspace label','Use letters, digits, underscore or hyphen, up to 40 characters.');return
    base=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'Palm92PrivateWorkspaces'
    root=base/workspace
    password=simpledialog.askstring('Unlock private workspace','Passphrase (at least 12 characters). There is no recovery if it is lost.',show='*')
    if not password:return
    if not (root/'database.vault').exists():
        again=simpledialog.askstring('Create private workspace','Confirm your new passphrase:',show='*')
        if password!=again:messagebox.showerror('Passphrase','The passphrases do not match.');return
    # Desktop private profile deliberately overrides inherited cloud settings.
    os.environ['PALM92_ALLOW_CLOUD_CONNECTORS']='NO'
    os.environ['PALM92_ENABLE_LIVE_SEND']='NO'
    try:
        store=Store(root,password)
        del password
        window.destroy()
        serve(root,store=store,open_browser=True)
    except Exception as exc:
        messagebox.showerror('Palm92 could not open',str(exc))


if __name__=='__main__':main()
