import psutil
for c in psutil.net_connections():
    if c.laddr.port == 8000 and c.pid:
        try:
            print(f"PID {c.pid}: {psutil.Process(c.pid).cmdline()}")
        except Exception as e:
            print(f"PID {c.pid}: {e}")
