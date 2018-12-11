"""
uds2.client
~~~~~~~~~~~

This module implements the Client for the Google API.
"""

import json

import requests

from .exceptions import APIError
from .files import UDS2File


BASE_URL = 'https://www.googleapis.com/drive/v3'

class Client(object):
    """ Handle the Google API.

    :param auth: an OAuth2 credential object.
    :param session: (optional) a session capable of making persistent
    HTTP requests. Defaults to `requests.Session()`.
    """

    def __init__(self, auth, session=None):
        self.auth = auth
        self.session = session or requests.Session()

        self.root = self.setup_root()
    
    def login(self):
        """ Authorize client. """
        if not self.auth.access_token \
            or (hasattr(self.auth, 'access_token_expired')
                and self.auth.access_token_expired):
            
            import httplib2; http = httplib2.Http()
            self.auth.refresh(http)
    
        self.session.headers.update({
            'Authorization': 'Bearer {}'.format(self.auth.access_token)})

    def request(self, method, url, **kwargs):
        """ Make a request. """
        response = getattr(self.session, method)(url, **kwargs)
        if response.ok:
            return response
        else:
            APIError(response)

    def setup_root(self):
        """ Get/create the `uds2_root` Drive folder. """
        r = self.request('get', '{}/files/'.format(BASE_URL),
                data={
                    'kind': 'drive#folder',
                    'name': 'uds2_root',
                    'q': 'properties has {key="uds2_root" and value="true"}'})
        
        data = json.loads(r.text)
        folders = data['files'] if 'files' in data else None
        if len(folders) == 0:
            root = self.create_root()
        elif len(folders) == 1:
            root = folders[0]
        else:
            print('[WARN] Multiple roots detected; returning first.')
            root = folders[0]
        
        return root
    
    def create_root(self):
        r = self.request('post', '{}/files'.format(BASE_URL),
            data={
                'name': 'uds2_root',
                'mimeType': 'application/vnd.google-apps.folder',
                'properties': {
                    'uds2_root': True},
                'parents': []})
        
        root = json.loads(r.text)
        return root
    
    def create_dump_folder(self, dump):
        """ Create a folder for a uds2 filedump.

        :param dump: a UDS2File object generated from a file.
        """
        r = self.request('post', '{}/files'.format(BASE_URL),
            data={
                'name': dump.name,
                'mimeType': 'application/vnd.google-apps.folder',
                'properties': {
                    'uds': True,
                    'size': dump.size,
                    'size_numeric': dump.nsize,
                    'size_encoded': dump.esize},
                'parents': dump.parents})
        
        folder = json.loads(r.text)
        return folder
    
    def get_files(self, folder=None):
        """ Get all uds2 files in a uds2 directory.
        
        :param folder: (optional) defines whether or not uds2 should get
        files from within a specified folder. The value supplied
        here must be a valid folder. Default folder is 'uds2_root'.
        """
        r = self.request('get', '{}/files'.format(BASE_URL),
            data={
                'q': 'properties has {key="uds2" and value="true"} ',
                'parents': [folder or 'uds2_root'],
                'pageSize': 1000})
        
        data = r.text
        raw_files = data.get('files', [])
        files = []
        for rf in raw_files:
            props = rf.get('properties')
            files.append(UDS2File(
                gid=rf.get('id'),
                name=rf.get('name'),
                mime=rf.get('mimeType'),
                parents=rf.get('parents'),
                size=rf.get('size'),
                nsize=props.get('size_numeric'),
                esize=props.get('encoded_size'),
                shared=props.get('shared'),
                data=None))
        
        return files
    
    def get_large_files(self, folder=None):
        """ Get all uds2 files in a large folder.

        This method serves the same function as `get_files`,
        but should be used for dump folders that contain over
        1000 files.

        :param folder: (optional) defines whether or not uds2 should get
        files from within a specified folder. The value supplied
        here must be a valid folder ID. Default folder is 'uds2_root'.
        """
        token = None
        dump = []
        while True:
            r = self.request('get', '{}/files'.format(BASE_URL),
                data={
                    'parents': [folder or 'uds2_root'],
                    'pageSize': 1000,
                    'pageToken': token,
                    'fields': 'nextPageToken, files(id, name, properties)'})
            
            data = json.loads(r)
            
            token = data['nextPageToken']

            page = data.get('files')
            dump.append(page)

        return dump            
