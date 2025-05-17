import re
import paramiko
import time

# Maximum buffer size for reading SSH responses
MAX_BUFFER = 65535

class RouterSSHClient:
    def __init__(self, host, username, password):
        # Initialize router connection details
        self.host = host
        self.username = username
        self.password = password
        self.ssh = paramiko.SSHClient()
        self.shell = None

        # Automatically add the host key if not already known
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        try:
            # Attempt to establish SSH connection to the router
            self.ssh.connect(
                hostname=self.host,
                username=self.username,
                password=self.password,
                look_for_keys=False,
                allow_agent=False
            )

            # Invoke an interactive shell session
            self.shell = self.ssh.invoke_shell()
            
            # Enter privileged EXEC mode
            self.shell.send("enable\n")
            time.sleep(1)

            # Send enable password (assumed to be 'admin')
            self.shell.send("admin\n")
            time.sleep(1)
        
            return True
        except Exception as e:
            print(f"[{self.host}] CONNECTION ERROR: {e}")
            return False

    def send_command(self, command):
        if not self.shell:
            return None

        # Send command to the router
        self.shell.send(command + "\n")
        time.sleep(2)
        
        # Read the command output
        output = ""
        while self.shell.recv_ready():
            output += self.shell.recv(MAX_BUFFER).decode("utf-8")
        return output

    def get_users(self):
        if not self.connect():
            return []

        # Retrieve the configuration lines with user definitions
        output = self.send_command("show running-config | include username")
        print(output)

        # Close SSH session
        self.close()

        # Parse user information using regex
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

        # Enter global configuration mode
        self.send_command("config t")
        time.sleep(1)

        # Send command to create the user
        command = f'username {username} privilege {privilege} secret {password}'
        self.send_command(command)

        # Close SSH session
        self.close()

        return { 
            "host": self.host, 
            "status": "created", 
            "privilege": privilege,
            "username": username,
        }

    def delete_user(self, username):
        if not self.connect():
            return { "host": self.host, "status": "failed" }

        # Enter global configuration mode
        self.send_command("config t")
        time.sleep(1)

        # Send command to delete the user
        command = f'no username {username}'
        self.send_command(command)

        # Close SSH session
        self.close()

        return { 
            "host": self.host, 
            "status": "deleted", 
            "username": username,
        }
    
    def update_user(self, old_username, new_username ,password, privilege):
        if not self.connect():
            return { "host": self.host, "status": "failed" }

        # Enter global configuration mode
        self.send_command("config t")
        time.sleep(1)

        # Delete the old user
        command = f'no username {old_username}'
        self.send_command(command)
        time.sleep(2)

        # Create the new user
        command = f'username {new_username} privilege {privilege} secret {password}'
        self.send_command(command)
        time.sleep(2)

        # Close SSH session
        self.close()

        return { 
            "host": self.host, 
            "status": "updated", 
            "privilege": privilege,
            "username": old_username,
            "auth_method": "secret" 
        }

    def close(self):
        # Exit the shell and close the SSH connection
        if self.shell:
            self.shell.send("exit\n")
            time.sleep(1)
        self.ssh.close()
