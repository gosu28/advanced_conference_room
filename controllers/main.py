import odoo.http as http
from odoo import SUPERUSER_ID
from odoo import registry as registry_get
from odoo.api import Environment
from odoo.addons.calendar.controllers.main import CalendarController



class ExtensionCalendarController(CalendarController):

    @http.route()
    def accept(self, db, token, action, id, **kwargs):
        registry = registry_get(db)
        with registry.cursor() as cr:
            env = Environment(cr, SUPERUSER_ID, {})
            attendee = env['calendar.attendee'].search([('access_token', '=', token), ('state', '!=', 'accepted')])
            if attendee:
                attendee.do_accept()
                user = env['res.users'].search([('partner_id', '=', attendee.partner_id.id)])
                if user:
                    event = env['mail.activity'].search([('res_id', '=', attendee.event_id.id),
                                                         ('user_id', '=', user.id), ('res_model', '=', 'calendar.event')])
                    event.action_done()
        return super(ExtensionCalendarController, self).view(db, token, action, id, view='form')

    @http.route()
    def declined(self, db, token, action, id):
        registry = registry_get(db)
        with registry.cursor() as cr:
            env = Environment(cr, SUPERUSER_ID, {})
            attendee = env['calendar.attendee'].search([('access_token', '=', token), ('state', '!=', 'declined')])
            if attendee:
                attendee.do_decline()
                user = env['res.users'].search([('partner_id', '=', attendee.partner_id.id)])
                if user:
                    event = env['mail.activity'].search([('res_id', '=', attendee.event_id.id),
                                                         ('user_id', '=', user.id), ('res_model', '=', 'calendar.event')])
                    event.action_done()
        return super(ExtensionCalendarController, self).view(db, token, action, id, view='form')
