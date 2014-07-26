import cherrypy
from modules.portal.auth import AuthController, require, member_of, name_is

class LoggedIn:
    _cp_config = {
        'auth.require': [member_of('admin')]
    }

    @cherrypy.expose
    def index(self):
        return """This is the admin only area."""

class Root:
    _cp_config = {
        'tools.sessions.on': True,
        'tools.auth.on': True
    }
    
    auth = AuthController()
    restricted = LoggedIn()

    @cherrypy.expose
    @require()
    def index(self):
        return "haha"

    @cherrypy.expose
    @require(name_is("joe"))
    def only_for_joe(self):
        return """Hello Joe - this page is available to you only"""

if __name__=="__main__":
    cherrypy.quickstart(Root())
