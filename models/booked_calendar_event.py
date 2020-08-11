from odoo import fields, models


class BookedCalendarEvent(models.Model):
    _name = 'booked.calendar.event'
    name = fields.Char('State')
    start = fields.Datetime('Start', required=True, help="Start date of an event, without time for full days events")
    stop = fields.Datetime('Stop', required=True, help="Stop date of an event, without time for full days events")
    booked_calendar_event_id = fields.Many2one('calendar.event', ondelete='cascade')
    location_room = fields.Many2one('conference.room', 'Location Room', readonly=True)
