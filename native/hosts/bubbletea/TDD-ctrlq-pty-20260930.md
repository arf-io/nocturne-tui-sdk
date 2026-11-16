# Bubble Tea quit keys

The Bubble Tea host quits on Ctrl-Q and on Ctrl-C. `test-ctrlq-pty.py` checks both keys against the compiled host.

The test starts `./bubbletea-host` with stdin, stdout and stderr on one pseudo-terminal. It waits for the alternate screen to open and for ICANON, ECHO and IXON to be off, so the host is in raw mode. It then waits 250 ms for Bubble Tea to finish starting up, sends the key byte, and requires the process to exit normally and the alternate screen to close. The same run repeats with Ctrl-C, sent as a key byte and not as a signal.

Build the host and run the test:

```sh
cd native/hosts/bubbletea
go build -o bubbletea-host .
python3 test-ctrlq-pty.py
```
