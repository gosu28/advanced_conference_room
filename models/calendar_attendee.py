from datetime import timedelta

import pytz
from pytz import timezone

from odoo import models, api, _
from odoo.exceptions import UserError


class Attendee(models.Model):
    _inherit = 'calendar.attendee'

    def do_accept(self):
        start = (self.event_id.start + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
        end = (self.event_id.stop - timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
        self.env.cr.execute('''SELECT partner_id, event_id FROM calendar_attendee WHERE event_id IN (
                                                                    SELECT id FROM calendar_event WHERE ((%s BETWEEN start AND stop)
                                                                                                         OR (%s BETWEEN start AND stop)) and active=TRUE)
                                                                    AND partner_id = %s AND state='accepted' AND event_id != %s
                                                                   ''',
                            (start, end, self.partner_id.id, self.event_id.id))
        all_current_partner_event = self.env.cr.fetchall()
        if all_current_partner_event and len(all_current_partner_event) > 0:
            current_event = self.env['calendar.event'].browse(all_current_partner_event[0][1])
            current_event_start = current_event.start_datetime.astimezone(timezone(self.get_timezone()))
            current_event_stop = current_event.stop_datetime.astimezone(timezone(self.get_timezone()))
            raise UserError(_(
                "You Can Not Join 2 Meetings At Same Time. You Did Join Meeting Name" + '"' + current_event.name + '" From ' +
                current_event_start.strftime("%d/%m/%Y %H:%M") + ' To ' + current_event_stop.strftime(
                    "%d/%m/%Y %H:%M")))
        result = super(Attendee, self).do_accept()
        return result

    def get_timezone(self):
        # get timezone
        user_time_zone = pytz.UTC
        if self.env.user.partner_id.tz:
            # change the timezone to the timezone of the user
            user_time_zone = pytz.timezone(self.env.user.partner_id.tz)
        return user_time_zone.zone
