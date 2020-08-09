# -*- coding: utf-8 -*-
from addons.resource.models.resource import HOURS_PER_DAY
from odoo import models, api


class CustomHolidaysRequest(models.Model):
    _inherit = "hr.leave"

    def _validate_leave_request(self):
        """ Validate leave requests (holiday_type='employee')
        by creating a calendar event and a resource leaves. """
        holidays = self.filtered(lambda request: request.holiday_type == 'employee')
        holidays._create_resource_leave()
        for holiday in holidays.filtered(lambda l: l.holiday_status_id.create_calendar_meeting):
            meeting_values = holiday._prepare_holidays_meeting_values()
            meeting = self.env['calendar.event'].with_context(no_mail_to_attendees=True,
                                                              force_create_by_leave=True).create(meeting_values)
            holiday.write({'meeting_id': meeting.id})
            # remove booked
            self.env['booked.calendar.event'].sudo().search([('booked_calendar_event_id', '=', meeting.id)]).unlink()

    def _prepare_holidays_meeting_values(self):
        self.ensure_one()
        calendar = self.employee_id.resource_calendar_id or self.env.company.resource_calendar_id
        meeting_values = {
            'name': self.display_name,
            'duration': self.number_of_days * (calendar.hours_per_day or HOURS_PER_DAY),
            'description': self.notes,
            'user_id': self.user_id.id,
            'start': self.date_from,
            'stop': self.date_to,
            'allday': False,
            'state': 'open',  # to block that meeting date in the calendar
            'privacy': 'confidential',
            'event_tz': self.user_id.tz,
            'activity_ids': [(5, 0, 0)],
            'is_leave': True
        }
        # Add the partner_id (if exist) as an attendee
        if self.user_id and self.user_id.partner_id:
            meeting_values['partner_ids'] = [
                (4, self.user_id.partner_id.id)]
        return meeting_values
