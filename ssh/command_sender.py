import re
import paramiko
import time

MAX_BUFFER = 65535

class RouterSSHClient:
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.ssh = paramiko.SSHClient()
        self.shell = None

        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        try:
            self.ssh.connect(
                hostname=self.host,
                username=self.username,
                password=self.password,
                look_for_keys=False,
                allow_agent=False
            )

            self.shell = self.ssh.invoke_shell()
            
            self.shell.send("enable\n")
            
            time.sleep(1)
            
            self.shell.send("admin\n")
            
            time.sleep(1)
            
            return True
        except Exception as e:
            print(f"[{self.host}] CONNECTION ERROR: {e}")
            
            return False

    def send_command(self, command):
        if not self.shell:
            return None

        self.shell.send(command + "\n")
        time.sleep(2)

        
        output = ""
        
        while self.shell.recv_ready():
            output += self.shell.recv(MAX_BUFFER).decode("utf-8")
        return output

    def get_users(self):
        if not self.connect():
            return []

        output = self.send_command("show running-config | include username")
        self.close()

        users = []
        pattern = r"username (\S+)(?: privilege (\d+))? secret(?: \d+)? ([^\n]+)"

        for line in output.splitlines():
            match = re.match(pattern, line.strip())
        
            if match:
                username = match.group(1)
                privilege = int(match.group(2)) if match.group(2) else 1

                users.append({
                    "username": username,
                    "privilege": privilege,
                    "auth_method": "secret",
                    "host": self.host
                })


        return users
    
    def create_user(self, username, privilege, password):
        if not self.connect():
            return { "host": self.host, "status": "failed" }

        self.send_command("config t")
        
        time.sleep(1)

        command = f'username {username} privilege {privilege} secret {password}'
        
        self.send_command(command)

        self.close()

        return { 
            "host": self.host, 
            "status": "created", 
            "privilege": privilege,
            "username": username,
            "auth_method": "secret" 
        }

    def delete_user(self, username):
        if not self.connect():
            return { "host": self.host, "status": "failed" }

        self.send_command("config t")
        
        time.sleep(1)

        command = f'no username {username}'
        
        self.send_command(command)

        self.close()

        return { 
            "host": self.host, 
            "status": "deleted", 
            "username": username,
        }
    
    def update_user(self, old_username, new_username ,password, privilege):
        if not self.connect():
            return { "host": self.host, "status": "failed" }
        

        self.send_command("config t")
        
        time.sleep(1)

        command = f'no username {old_username}'

        self.send_command(command)

        time.sleep(1)

        command = f'username {new_username} privilege {privilege} secret {password}'
        
        self.send_command(command)

        self.close()

        return { 
            "host": self.host, 
            "status": "updated", 
            "privilege": privilege,
            "username": old_username,
            "auth_method": "secret" 
        }

    def close(self):
        if self.shell:
            self.shell.send("exit\n")
            time.sleep(1)
        self.ssh.close()
