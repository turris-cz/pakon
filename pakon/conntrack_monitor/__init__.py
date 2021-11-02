import subprocess



process = subprocess.Popen(["ssh","root@10.0.0.1", "/tmp/bin/conntrack-watch", "-e"], stdout=subprocess.PIPE)


for i in range(10):
    print(process.stdout.read())
