#!/usr/bin/env python
import webapp2
from google.appengine.ext import db
from google.appengine.api import memcache
import string
import random
import jinja2
import os
import time
import logging

SECONDS = 100

# Setup JINJA templates
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])


def id_generator(size=8, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for x in range(size))


class TimeLapseMessage(db.Model):
    message = db.TextProperty(required=True)
    timestamp = db.IntegerProperty(required=True)


####################
# Request Handlers #
####################

class MessageHandler(webapp2.RequestHandler):
    def get(self, id):
        result = memcache.get("message:%s" % id)
        if result is not None:
            template = JINJA_ENVIRONMENT.get_template('templates/message.html')
            current_timestamp = int(round(time.time() * 1000))
            if current_timestamp - result.timestamp > SECONDS * 1000:
                memcache.delete("message:%s" % id)
                self.abort(404)

            seconds_left = SECONDS - (current_timestamp - result.timestamp) / 1000
            self.response.write(template.render({'message': result.message,
                                                 'seconds_left': seconds_left}))
        else:
            self.abort(404)


class MessageDisappearedHandler(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/disappeared.html')
        self.response.write(template.render({}))


class MainHandler(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('templates/index.html')
        self.response.write(template.render({}))

    def post(self):
        message = self.request.get("message")
        if len(message) > 0:
            id = id_generator()
            timelapse_message = TimeLapseMessage(
                message=message[0:5000],
                timestamp=int(round(time.time() * 1000))
            )
            memcache.add("message:%s" % id, timelapse_message, time=SECONDS)
            self.redirect("/msg/%s" % id)


##################
# Error Handlers #
##################

def handle_404(request, response, exception):
    template = JINJA_ENVIRONMENT.get_template('templates/exceptions/404.html')
    response.write(template.render({}))
    response.set_status(404)


# Map URLs to handlers
app = webapp2.WSGIApplication([
    ('/msg/([^/]+)?', MessageHandler),
    ('/disappeared', MessageDisappearedHandler),
    ('/', MainHandler)
], debug=True)


app.error_handlers[404] = handle_404