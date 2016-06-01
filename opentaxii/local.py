from werkzeug.local import Local, LocalManager

context = Local()
local_manager = LocalManager([context])


def release_context():
    local_manager.cleanup()
