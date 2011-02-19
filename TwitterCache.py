

class TwitterCache(object):
    def __init__(self, t):
        """
        @param t Twitter API instance.
        """
        self._twitter = t
        pass

        #self.MAX_GETFOLLOWERS_AGE = 60 * 60
        #self.MAX_GETFRIENDS_AGE = 60 * 60 * 6
        #self.MAX_GETUSER_AGE = 86400 * 30

    def getFollowerIDs(self, **kw):
        #update = True
        #try:
        #    # Read from cache if we can.
        #    with open('cache/getFollowerIDs/%s.pickle' % self._twitter._consumer_key, 'rb') as fh:
        #        data,lastupdated = pickle.load(fh)
        #        if time() - lastupdated < self.MAX_GETFOLLOWERS_AGE:
        #            # The record is not that old, so don't update.
        #            update = False
        #except IOError:
        #    pass
        #if update:
        if 1 == 1:
            self._twitter.next_cursor = -1
            data = []
            while self._twitter.next_cursor != 0:
                _followers = self._twitter.getFollowerIDs(self._twitter.next_cursor, **kw)
                for f in _followers:
                    data.append(f)
            #_followers = self._twitter.getFollowerIDs(**kw)
        #    with open('cache/getFollowerIDs/%s.pickle' % self._twitter._consumer_key, 'wb') as fh:
        #        pickle.dump((data, time()), fh)
        return data

    def getFollowers(self, **kw):
        #update = True
        #try:
        #    # Read from cache if we can.
        #    with open('cache/getFollowers/%s.pickle' % self._twitter._consumer_key, 'rb') as fh:
        #        data,lastupdated = pickle.load(fh)
        #        if time() - lastupdated < self.MAX_GETFOLLOWERS_AGE:
        #            # The record is not that old, so don't update.
        #            update = False
        #except IOError:
        #    pass
        #if update:
        if 1 == 1:
            self._twitter.next_cursor = -1
            data = []
            while self._twitter.next_cursor != 0:
                _followers = self._twitter.getFollowers(self._twitter.next_cursor, **kw)
                for f in _followers:
                    data.append(f)
        #    with open('cache/getFollowers/%s.pickle' % self._twitter._consumer_key, 'wb') as fh:
        #        pickle.dump((data, time()), fh)
        return data

    def getFriends(self, name=None, **kw):
        #update = True
        #try:
        #    # Read from cache if we can.
        #    with open('cache/getFriends/%s.pickle' % name, 'rb') as fh:
        #        data,lastupdated = pickle.load(fh)
        #        if time() - lastupdated < self.MAX_GETFRIENDS_AGE:
        #            # The record is not that old, so don't update.
        #            update = False
        #except IOError:
        #    pass
        #if update:
        if 1 == 1:
            self._twitter.next_cursor = -1
            data = []
            while self._twitter.next_cursor != 0:
                _friends = self._twitter.getFriends(name, self._twitter.next_cursor, **kw)
                for f in _friends:
                    data.append(f)
        #    with open('cache/getFriends/%s.pickle' % name, 'wb') as fh:
        #        pickle.dump((data, time()), fh)
        return data

    def getUser(self, username, **kw):
        #update = True
        #try:
        #    # Read from cache if we can.
        #    with open('cache/GetUser/%s.pickle' % username, 'rb') as fh:
        #        user,lastupdated = pickle.load(fh)
        #        if time() - lastupdated < self.MAX_GETUSER_AGE:
        #            # The record is not that old, so don't update.
        #            update = False
        #except IOError:
        #    pass
        #if update:
        if 1 == 1:
            user = self._twitter.GetUser(username, **kw)
        #    with open('cache/GetUser/%s.pickle' % username, 'wb') as fh:
        #        pickle.dump((user, time()), fh)
        return user

