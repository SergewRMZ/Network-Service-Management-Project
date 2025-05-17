from ssh.command_sender import RouterSSHClient

class UserService:
    def __init__(self, routers):
        self.routers = routers

    def _get_router(self, host):
        for router in self.routers:
            if router["ip"] == host or router.get("hostname") == host:
                return router
        return None

    def get_all_users(self):
        all_users = []
        for router in self.routers:
            client = RouterSSHClient(router["ip"], router["username"], router["password"])
            users = client.get_users()
            for user in users:
                user_info = {
                    "username": user["username"],
                    "privilege": user["privilege"],
                    "router": router["ip"]
                }
                all_users.append(user_info)
        return all_users

    def get_users_by_router(self, host):
        router = self._get_router(host)
        if not router:
            return None

        client = RouterSSHClient(router["ip"], router["username"], router["password"])
        users = client.get_users()
        for user in users:
            user["router"] = router["ip"]
        return users

    def create_user(self, new_user):
        results = []
        for router in self.routers:
            client = RouterSSHClient(router["ip"], router["username"], router["password"])
            result = client.create_user(
                new_user["username"],
                new_user["privilege"],
                new_user["password"]
            )
            result["router"] = router["ip"]
            results.append(result)
        return results

    def create_user_on_router(self, host, new_user):
        router = self._get_router(host)
        if not router:
            return None
        client = RouterSSHClient(router["ip"], router["username"], router["password"])
        result = client.create_user(
            new_user["username"],
            new_user["privilege"],
            new_user["password"]
        )
        result["router"] = router["ip"]
        return result

    def delete_user(self, username):
        results = []
        for router in self.routers:
            client = RouterSSHClient(router["ip"], router["username"], router["password"])
            result = client.delete_user(username)
            result["router"] = router["ip"]
            results.append(result)
        return results

    def delete_user_on_router(self, host, username):
        router = self._get_router(host)
        if not router:
            return None
        client = RouterSSHClient(router["ip"], router["username"], router["password"])
        result = client.delete_user(username)
        result["router"] = router["ip"]
        return result

    def update_users(self, old_username, new_user):
        results = []
        for router in self.routers:
            client = RouterSSHClient(router["ip"], router["username"], router["password"])
            result = client.update_user(
                old_username,
                new_user["username"],
                new_user["password"],
                new_user["privilege"]
            )
            result["router"] = router["ip"]
            results.append(result)
        return results

    def update_user_on_router(self, host, old_username, new_user):
        router = self._get_router(host)
        if not router:
            return None
        client = RouterSSHClient(router["ip"], router["username"], router["password"])
        result = client.update_user(
            old_username,
            new_user["username"],
            new_user["password"],
            new_user["privilege"],
        )
        result["router"] = router["ip"]
        return result
