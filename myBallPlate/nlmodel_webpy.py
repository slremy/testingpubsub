from nlmodel import *
import web

web.config.debug = False;
header = web.header
urls = (
        '/', 'index',
        '/init','initModel',
        '/state','state',
        '/u','model',
        '/stop','closeModel'
        )

app = web.application(urls, globals())
render = web.template.render('.')

class closeModel:
    def GET(self):
        return exit(0)
    def POST(self):
        return exit(0)

class index:
    def GET(self):
        return render.index2();

class initModel:
    def GET(self):
        return self.process();
    def POST(self):
        return self.process();
    def process(self):
        i = web.input();
        data = i;
        f = initModel_process(web.ctx.query);
        header("Content-Type", "text/plain") # Set the Header
        return f

class state:
    def GET(self):
        return self.process();
    def POST(self):
        return self.process();
    def process(self):
        f = state_process();
        header("Content-Type", "text/plain") # Set the Header
        return f

class model:
    def GET(self):
        return self.process();
    def POST(self):
        return self.process();
    def process(self):
        f = interpret(web.ctx.path+web.ctx.query);
        header("Content-Type", "text/plain") # Set the Header
        return f


if __name__ == "__main__":
    
    signal.signal(signal.SIGALRM, updateState)
    signal.setitimer(signal.ITIMER_REAL, h, h)
  
    wsgifunc = app.wsgifunc()
    wsgifunc = web.httpserver.StaticMiddleware(wsgifunc)
    server = web.httpserver.WSGIServer(("0.0.0.0", port),wsgifunc)
    print "http://%s:%d/" % ("0.0.0.0", port)

    #wait until you can't listen anymore
    try:
        server.start()
    except (KeyboardInterrupt, SystemExit):
        server.stop()
        print exc_info()
        signal.setitimer(signal.ITIMER_REAL, 0, h)
        print "Shutting down service"
