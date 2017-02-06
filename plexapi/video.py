# -*- coding: utf-8 -*-
from plexapi import media, utils
from plexapi.exceptions import NotFound
from plexapi.base import Playable, PlexPartialObject


class Video(PlexPartialObject):
    TYPE = None

    def _loadData(self, data):
        """ Used to set the attributes. """
        self._data = data
        self.listType = 'video'
        self.addedAt = utils.toDatetime(data.attrib.get('addedAt'))
        self.key = data.attrib.get('key')
        self.lastViewedAt = utils.toDatetime(data.attrib.get('lastViewedAt'))
        self.librarySectionID = data.attrib.get('librarySectionID')
        self.ratingKey = utils.cast(int, data.attrib.get('ratingKey'))
        self.summary = data.attrib.get('summary')
        self.thumb = data.attrib.get('thumb')
        self.title = data.attrib.get('title')
        self.titleSort = data.attrib.get('titleSort', self.title)
        self.type = data.attrib.get('type')
        self.updatedAt = utils.toDatetime(data.attrib.get('updatedAt'))
        self.viewCount = utils.cast(int, data.attrib.get('viewCount', 0))

    @property
    def thumbUrl(self):
        """Return url to thumb image."""
        if self.thumb:
            return self._root.url(self.thumb)

    def analyze(self):
        """The primary purpose of media analysis is to gather information about
        that mediaitem. All of the media you add to a Library has properties
        that are useful to know–whether it's a video file,
        a music track, or one of your photos.
        """
        self._root.query('/%s/analyze' % self.key.lstrip('/'), method=self._root._session.put)

    def markWatched(self):
        """Mark a items as watched."""
        path = '/:/scrobble?key=%s&identifier=com.plexapp.plugins.library' % self.ratingKey
        self._root.query(path)
        self.reload()

    def markUnwatched(self):
        """Mark a item as unwatched."""
        path = '/:/unscrobble?key=%s&identifier=com.plexapp.plugins.library' % self.ratingKey
        self._root.query(path)
        self.reload()

    def refresh(self):
        """Refresh a item."""
        self._root.query('%s/refresh' %
                          self.key, method=self._root._session.put)

    def section(self):
        """Library section."""
        return self._root.library.sectionByID(self.librarySectionID)


@utils.register_libtype
class Movie(Video, Playable):
    TYPE = 'movie'

    def _loadData(self, data):
        """Used to set the attributes

        Args:
            data (Element): XML reponse from PMS as Element
                            normally built from server.query
        """
        Video._loadData(self, data)
        Playable._loadData(self, data)
        self.art = data.attrib.get('art')
        self.audienceRating = utils.cast(
            float, data.attrib.get('audienceRating'))
        self.audienceRatingImage = data.attrib.get('audienceRatingImage')
        self.chapterSource = data.attrib.get('chapterSource')
        self.contentRating = data.attrib.get('contentRating')
        self.duration = utils.cast(int, data.attrib.get('duration'))
        self.guid = data.attrib.get('guid')
        self.originalTitle = data.attrib.get('originalTitle')
        self.originallyAvailableAt = utils.toDatetime(
            data.attrib.get('originallyAvailableAt'), '%Y-%m-%d')
        self.primaryExtraKey = data.attrib.get('primaryExtraKey')
        self.rating = data.attrib.get('rating')
        self.ratingImage = data.attrib.get('ratingImage')
        self.studio = data.attrib.get('studio')
        self.tagline = data.attrib.get('tagline')
        self.userRating = utils.cast(float, data.attrib.get('userRating'))
        self.viewOffset = utils.cast(int, data.attrib.get('viewOffset', 0))
        self.year = utils.cast(int, data.attrib.get('year'))
        self.collections = self._buildSubitems(data, media.Collection)
        self.countries = self._buildSubitems(data, media.Country)
        self.directors = self._buildSubitems(data, media.Director)
        self.fields = self._buildSubitems(data, media.Field)
        self.genres = self._buildSubitems(data, media.Genre)
        self.media = self._buildSubitems(data, media.Media)
        self.producers = self._buildSubitems(data, media.Producer)
        self.roles = self._buildSubitems(data, media.Role)
        self.writers = self._buildSubitems(data, media.Writer)
        # self.videoStreams = utils.findStreams(self.media, 'videostream')  # these dont go here
        # self.audioStreams = utils.findStreams(self.media, 'audiostream')  # these dont go here
        # self.subtitleStreams = utils.findStreams(self.media, 'subtitlestream')  # these dont go here

    @property
    def actors(self):
        return self.roles

    @property
    def isWatched(self):
        return bool(self.viewCount > 0)

    @property
    def location(self):
        """ This does not exist in plex xml response but is added to have a common
            interface to get the location of the Movie/Show/Episode
        """
        files = [i.file for i in self.iterParts() if i]
        if len(files) == 1:
            files = files[0]

        return files

    def download(self, savepath=None, keep_orginal_name=False, **kwargs):
        downloaded = []
        locs = [i for i in self.iterParts() if i]
        for loc in locs:
            if keep_orginal_name is False:
                name = '%s.%s' % (self.title.replace(' ', '.'), loc.container)
            else:
                name = loc.file
            # So this seems to be a alot slower but allows transcode.
            if kwargs:
                download_url = self.getStreamURL(**kwargs)
            else:
                download_url = self._root.url('%s?download=1' % loc.key)
            dl = utils.download(download_url, filename=name, savepath=savepath, session=self._root._session)
            if dl:
                downloaded.append(dl)
        return downloaded


@utils.register_libtype
class Show(Video):
    TYPE = 'show'

    def _loadData(self, data):
        Video._loadData(self, data)
        # fix the key if this was loaded from search..
        self.key = self.key.replace('/children', '')
        self.art = data.attrib.get('art')
        self.banner = data.attrib.get('banner')
        self.childCount = utils.cast(int, data.attrib.get('childCount'))
        self.contentRating = data.attrib.get('contentRating')
        self.duration = utils.cast(int, data.attrib.get('duration'))
        self.guid = data.attrib.get('guid')
        self.index = data.attrib.get('index')
        self.leafCount = utils.cast(int, data.attrib.get('leafCount'))
        self.location = utils.findLocations(data, single=True) or None
        self.originallyAvailableAt = utils.toDatetime(
            data.attrib.get('originallyAvailableAt'), '%Y-%m-%d')
        self.rating = utils.cast(float, data.attrib.get('rating'))
        self.studio = data.attrib.get('studio')
        self.theme = data.attrib.get('theme')
        self.viewedLeafCount = utils.cast(int, data.attrib.get('viewedLeafCount'))
        self.year = utils.cast(int, data.attrib.get('year'))
        self.genres = self._buildSubitems(data, media.Genre)
        self.roles = self._buildSubitems(data, media.Role)

    @property
    def actors(self):
        return self.roles

    @property
    def isWatched(self):
        return bool(self.viewedLeafCount == self.leafCount)

    def seasons(self):
        """Returns a list of Season."""
        key = '/library/metadata/%s/children' % self.ratingKey
        return self._fetchItems(key, Season.TYPE)

    def season(self, title=None):
        """ Returns the season with the specified title or number.

            Parameters:
                title (str or int): Title or Number of the season to return.
        """
        if isinstance(title, int):
            title = 'Season %s' % title
        key = '/library/metadata/%s/children' % self.ratingKey
        return self._fetchItem(key, title)

    def episodes(self, watched=None):
        """Returs a list of Episode

           Args:
                watched (bool): Defaults to None. Exclude watched episodes
        """
        leavesKey = '/library/metadata/%s/allLeaves' % self.ratingKey
        return utils.listItems(self._root, leavesKey, watched=watched)

    def episode(self, title=None, season=None, episode=None):
        """Find a episode using a title or season and episode.

           Note:
                Both season and episode is required if title is missing.

           Args:
                title (str): Default None
                season (int): Season number, default None
                episode (int): Episode number, default None

           Raises:
                ValueError: If season and episode is missing.
                NotFound: If the episode is missing.

           Returns:
                Episode

           Examples:
                >>> plex.search('The blacklist')[0].episode(season=1, episode=1)
                <Episode:116263:The.Freelancer>
                >>> plex.search('The blacklist')[0].episode('The Freelancer')
                <Episode:116263:The.Freelancer>

        """
        if not title and (not season or not episode):
            raise TypeError('Missing argument: title or season and episode are required')
        if title:
            path = '/library/metadata/%s/allLeaves' % self.ratingKey
            return utils.findItem(self._root, path, title)
        elif season and episode:
            results = [i for i in self.episodes() if i.seasonNumber == season and i.index == episode]
            if results:
                return results[0]
            raise NotFound('Couldnt find %s S%s E%s' % (self.title, season, episode))

    def watched(self):
        """Return a list of watched episodes"""
        return self.episodes(watched=True)

    def unwatched(self):
        """Return a list of unwatched episodes"""
        return self.episodes(watched=False)

    def get(self, title):
        """Get a Episode with a title.

           Args:
                title (str): fx Secret santa
        """
        return self.episode(title)

    def analyze(self):
        """ """
        raise 'Cant analyse a show'  # fix me

    def refresh(self):
        """Refresh the metadata."""
        self._root.query('/library/metadata/%s/refresh' % self.ratingKey, method=self._root._session.put)

    def download(self, savepath=None, keep_orginal_name=False, **kwargs):
        downloaded = []
        for ep in self.episodes():
            dl = ep.download(savepath=savepath, keep_orginal_name=keep_orginal_name, **kwargs)
            if dl:
                downloaded.extend(dl)
        return downloaded


@utils.register_libtype
class Season(Video):
    TYPE = 'season'

    def _loadData(self, data):
        """Used to set the attributes

        Args:
            data (Element): Usually built from server.query
        """
        Video._loadData(self, data)
        self.key = self.key.replace('/children', '')
        self.leafCount = utils.cast(int, data.attrib.get('leafCount'))
        self.index = utils.cast(int, data.attrib.get('index'))
        self.parentKey = data.attrib.get('parentKey')
        self.parentRatingKey = utils.cast(int, data.attrib.get('parentRatingKey'))
        self.parentTitle = data.attrib.get('parentTitle')
        self.viewedLeafCount = utils.cast(int, data.attrib.get('viewedLeafCount'))

    @property
    def isWatched(self):
        return bool(self.viewedLeafCount == self.leafCount)

    @property
    def seasonNumber(self):
        """Returns season number."""
        return self.index

    def episodes(self, watched=None):
        """ Returs a list of Episode

           Parameters:
                watched (bool): Defaults to None. Exclude watched episodes
        """
        key = '/library/metadata/%s/children' % self.ratingKey
        return self._fetchItems(key, Episode.TYPE)
        # childrenKey = '/library/metadata/%s/children' % self.ratingKey
        # return utils.listItems(self._root, childrenKey, watched=watched)

    def episode(self, title=None, episode=None):
        """Find a episode using a title or season and episode.

           Note:
                episode is required if title is missing.

           Args:
                title (str): Default None
                episode (int): Episode number, default None

           Raises:
                TypeError: If title and episode is missing.
                NotFound: If that episode cant be found.

           Returns:
                Episode

           Examples:
                >>> plex.search('The blacklist').season(1).episode(episode=1)
                <Episode:116263:The.Freelancer>
                >>> plex.search('The blacklist').season(1).episode('The Freelancer')
                <Episode:116263:The.Freelancer>

        """
        if not title and not episode:
            raise TypeError('Missing argument, you need to use title or episode.')
        if title:
            path = '/library/metadata/%s/children' % self.ratingKey
            return utils.findItem(self._root, path, title)
        elif episode:
            results = [i for i in self.episodes() if i.seasonNumber == self.index and i.index == episode]
            if results:
                return results[0]
            raise NotFound('Couldnt find %s.Season %s Episode %s.' % (self.grandparentTitle, self.index. episode))

    def get(self, title):
        """Get a episode with a matching title.

           Args:
                title (str): fx Secret santa

            Returns:
                Episode
        """
        return self.episode(title)

    def show(self):
        """Return this seasons show."""
        return utils.listItems(self._root, self.parentKey)[0]

    def watched(self):
        """Returns a list of watched Episode"""
        return self.episodes(watched=True)

    def unwatched(self):
        """Returns a list of unwatched Episode"""
        return self.episodes(watched=False)

    def __repr__(self):
        clsname = self.__class__.__name__
        key = self.key.replace('/library/metadata/', '').replace('/children', '') if self.key else 'NA'
        title = self.title.replace(' ', '.')[0:20].encode('utf8')
        return '<%s:%s:%s:%s>' % (clsname, key, self.parentTitle, title)

    def download(self, savepath=None, keep_orginal_name=False, **kwargs):
        downloaded = []
        for ep in self.episodes():
            dl = ep.download(savepath=savepath, keep_orginal_name=keep_orginal_name, **kwargs)
            if dl:
                downloaded.extend(dl)
        return downloaded


@utils.register_libtype
class Episode(Video, Playable):
    TYPE = 'episode'

    def _loadData(self, data):
        """Used to set the attributes

            Args:
                data (Element): Usually built from server.query
        """
        Video._loadData(self, data)
        Playable._loadData(self, data)
        self._seasonNumber = None  # cached season number
        self.art = data.attrib.get('art')
        self.chapterSource = data.attrib.get('chapterSource')
        self.contentRating = data.attrib.get('contentRating')
        self.duration = utils.cast(int, data.attrib.get('duration'))
        self.grandparentArt = data.attrib.get('grandparentArt')
        self.grandparentKey = data.attrib.get('grandparentKey')
        self.grandparentRatingKey = utils.cast(int, data.attrib.get('grandparentRatingKey'))
        self.grandparentTheme = data.attrib.get('grandparentTheme')
        self.grandparentThumb = data.attrib.get('grandparentThumb')
        self.grandparentTitle = data.attrib.get('grandparentTitle')
        self.guid = data.attrib.get('guid')
        self.index = utils.cast(int, data.attrib.get('index'))
        self.originallyAvailableAt = utils.toDatetime(data.attrib.get('originallyAvailableAt'), '%Y-%m-%d')
        self.parentIndex = data.attrib.get('parentIndex')
        self.parentKey = data.attrib.get('parentKey')
        self.parentRatingKey = utils.cast(int, data.attrib.get('parentRatingKey'))
        self.parentThumb = data.attrib.get('parentThumb')
        self.rating = utils.cast(float, data.attrib.get('rating'))
        self.viewOffset = utils.cast(int, data.attrib.get('viewOffset', 0))
        self.year = utils.cast(int, data.attrib.get('year'))
        self.directors = self._buildSubitems(data, media.Director)
        self.media = self._buildSubitems(data, media.Media)
        self.writers = self._buildSubitems(data, media.Writer)
        # self.videoStreams = utils.findStreams(self.media, 'videostream')
        # self.audioStreams = utils.findStreams(self.media, 'audiostream')
        # self.subtitleStreams = utils.findStreams(self.media, 'subtitlestream')
        # data for active sessions and history
        self.sessionKey = utils.cast(int, data.attrib.get('sessionKey'))
        self.username = utils.findUsername(data)
        self.player = utils.findPlayer(self._root, data)
        self.transcodeSession = utils.findTranscodeSession(self._root, data)

    def __repr__(self):
        clsname = self.__class__.__name__
        key = self.key.replace('/library/metadata/', '').replace('/children', '') if self.key else 'NA'
        title = self.title.replace(' ', '.')[0:20].encode('utf8')
        return '<%s:%s:%s:S%s:E%s:%s>' % (clsname, key, self.grandparentTitle, self.seasonNumber, self.index, title)

    @property
    def isWatched(self):
        """Returns True if watched, False if not."""
        return bool(self.viewCount > 0)

    @property
    def seasonNumber(self):
        """Return this episode seasonnumber."""
        if self._seasonNumber is None:
            self._seasonNumber = self.parentIndex if self.parentIndex else self.season().seasonNumber
        return utils.cast(int, self._seasonNumber)

    @property
    def thumbUrl(self):
        """Return url to thumb image."""
        if self.grandparentThumb:
            return self._root.url(self.grandparentThumb)

    def season(self):
        """Return this episode Season"""
        return utils.listItems(self._root, self.parentKey)[0]

    def show(self):
        """Return this episodes Show"""
        return utils.listItems(self._root, self.grandparentKey)[0]

    @property
    def location(self):
        """ This does not exist in plex xml response but is added to have a common
            interface to get the location of the Movie/Show
        """
        # Note this should probably belong to some parent.
        files = [i.file for i in self.iterParts() if i]
        if len(files) == 1:
            files = files[0]
        return files

    def _prettyfilename(self):
        return '%s.S%sE%s' % (self.grandparentTitle.replace(' ', '.'),
            str(self.seasonNumber).zfill(2), str(self.index).zfill(2))
