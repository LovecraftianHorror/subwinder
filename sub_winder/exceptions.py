class SubWinderError(Exception):
    pass


class SubLangError(SubWinderError):
    pass


class SubAuthError(SubWinderError):
    pass


class SubUploadError(SubWinderError):
    pass


class SubDownloadError(SubWinderError):
    pass
