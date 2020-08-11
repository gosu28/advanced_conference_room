from datetime import datetime, timedelta
import pytz
from pytz import timezone
from odoo import fields, models
from odoo.exceptions import AccessError, UserError


class BookedCalendarEvent(models.Model):
    _name = 'booked.calendar.event'
    name = fields.Char('State')
    start = fields.Datetime('Start', required=True, help="Start date of an event, without time for full days events")
    stop = fields.Datetime('Stop', required=True, help="Stop date of an event, without time for full days events")
    booked_calendar_event_id = fields.Many2one('calendar.event', ondelete='cascade')
    location_room = fields.Many2one('conference.room', 'Location Room', readonly=True)
    calendar_id = fields.Char(string='Calendar Event', store=True)

    def create(self, vals):
        res = super(BookedCalendarEvent, self).create(vals)
        not_duplicate_ids = self.env['booked.calendar.event'].sudo().search(
            ['|', '|', ('calendar_id', '=', False), ('location_room', '!=', res.location_room.id),
             '|',
             ('start', '>=', res.stop), ('stop', '<=', res.start)])
        if not_duplicate_ids:
            need_to_check = self.env['booked.calendar.event'].sudo().search(
                [('calendar_id', '!=', False), ('location_room', '=', res.location_room.id),
                 ('id', 'not in', not_duplicate_ids.ids), ('id', '!=', res.id)])
            if need_to_check:
                raise UserError("Can not create this calendar because of existing a event same time in future")
        partner_list = []
        not_duplicate_partner_ids = self.env['booked.calendar.event'].sudo().search(
            ['|', ('calendar_id', '=', False),
             '|',
             ('start', '>=', res.stop), ('stop', '<=', res.start)])
        if not_duplicate_partner_ids:
            need_to_check_booked_event = self.env['booked.calendar.event'].sudo().read_group(
                [('id', 'not in', not_duplicate_partner_ids.ids)], ['booked_calendar_event_id'], ['id'])
            if need_to_check_booked_event:

        return res
