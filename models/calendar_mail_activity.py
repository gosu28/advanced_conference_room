from datetime import date, timedelta, datetime
import pytz
from odoo import api, models, _
from odoo.http import request


class CalendarMailActivity(models.Model):
    _name = 'calendar.event'
    _inherit = ['calendar.event', 'mail.thread', 'mail.activity.mixin']

    def get_timezone(self):
        # get timezone
        user_time_zone = pytz.UTC
        if self.env.user.partner_id.tz:
            # change the timezone to the timezone of the user
            user_time_zone = pytz.timezone(self.env.user.partner_id.tz)
        return user_time_zone.zone

    @api.model
    def create(self, values):
        if values.get('create_by_duplicate') == False:
            res = super(CalendarMailActivity, self).create(values)
            if values.get('recurrency') == True:
                calendar_id = self.env['calendar.event'].search([('recurrency', '=', True)])
                all_fake_booked_id = []
                for r in calendar_id.ids:
                    booked_calendar_id = r.split('-')[0]
                    all_fake_booked_id.append(booked_calendar_id)
                max_value = max(all_fake_booked_id)
                filter_value = [value for index, value in enumerate(all_fake_booked_id) if value == max_value]
                filter_calendar_ids = self.env['calendar.event'].search([('recurrency', '=', True)],
                                                                        limit=len(filter_value))
                # Create fake records into the database
                if filter_calendar_ids:
                    for rec in filter_calendar_ids:
                        calendar_id = rec.id
                        id_recurrent = rec.id.split('-')[0]
                        for a in rec.location_rooms:
                            room_id = a.id
                            convert_stop_date = rec.stop
                            stop_date = datetime.strptime(convert_stop_date, '%Y-%m-%d %H:%M:%S') + timedelta(
                                hours=(rec.duration - 1))
                            rec.env['booked.calendar.event'].sudo().create({
                                'name': a.name,
                                'start': rec.start,
                                'stop': stop_date,
                                'booked_calendar_event_id': id_recurrent,
                                'location_room': room_id,
                                'calendar_id': calendar_id
                            })
            partner_ids = []
            state = ['accepted', 'declined']
            attendee_ids = res.env['calendar.attendee'].sudo().search([('event_id', '=', res.id)])
            for attendee_id in attendee_ids:
                if attendee_id.state not in state:
                    partner_ids.append(attendee_id.partner_id.id)
            user_ids = res.env['res.users'].sudo().search([('partner_id', '=', partner_ids)])
            for user_id in user_ids:
                res.activity_schedule('advanced_conference_room.mail_act_meeting', date_deadline=date.today(),
                                      user_id=user_id.id, automated=True, calendar_event_id=res.id)
            return res
        else:
            res = super(CalendarMailActivity, self).create(values)
            return res

    def write(self, values):
        # self.ensure_one()
        for rec in self:
            if values.get('partner_ids'):
                state = ['accepted', 'declined']
                old_user_ids = [e.user_id.id for e in rec.env['mail.activity'].sudo().search(
                    [('res_id', '=', rec.id), ('res_model', '=', 'calendar.event')])]
                new_user_ids = [e.id for e in rec.env['res.users'].sudo().search(
                    [('partner_id', '=', values.get('partner_ids')[0][-1])])]
                user_ids = old_user_ids + new_user_ids
                users = rec.env['res.users'].sudo().search([('id', '=', user_ids)])
                for user_id in users:
                    attendee_id = rec.env['calendar.attendee'].sudo().search(
                        [('event_id', '=', rec.id), ('partner_id', '=', user_id.partner_id.id)])
                    if attendee_id:
                        if attendee_id.state not in state:
                            if user_id.id in new_user_ids and user_id.id not in old_user_ids:
                                rec.activity_schedule('advanced_conference_room.mail_act_meeting',
                                                      date_deadline=date.today(),
                                                      user_id=user_id.id, automated=True)
                            if user_id.id in old_user_ids and user_id.id not in new_user_ids:
                                rec.env['mail.activity'].sudo().search(
                                    [('res_id', '=', rec.id), ('res_model', '=', 'calendar.event'),
                                     ('user_id', '=', user_id.id)]).unlink()
                    else:
                        rec.activity_schedule('advanced_conference_room.mail_act_meeting', date_deadline=date.today(),
                                              user_id=user_id.id, automated=True, calendar_event_id=rec.id)

            return super(CalendarMailActivity, self).write(values)

    # def unlink(self):
    #     for rec in self:
    #         rec.env['mail.activity'].sudo().search(
    #             [('res_id', '=', rec.id), ('res_model', '=', 'calendar.event')]).unlink()
    #     return super(CalendarMailActivity, self).unlink()

    def compute_join_attendee(self):
        event = self.env['calendar.attendee'].sudo().search([('event_id', '=', self.id)])
        user = self.env['res.users'].sudo().search([('id', '=', request.session.uid)])
        state = ['accepted', 'declined']
        for e in event:
            if e.partner_id.id == user.partner_id.id:
                e.do_accept()
                if e.state in state:
                    self.env['mail.activity'].sudo().search(
                        [('res_id', '=', self.id), ('user_id', '=', self.env.uid)]).action_done()

    def compute_decline_attendee(self):
        event = self.env['calendar.attendee'].sudo().search([('event_id', '=', self.id)])
        user = self.env['res.users'].sudo().search([('id', '=', request.session.uid)])
        state = ['accepted', 'declined']
        for e in event:
            if e.partner_id.id == user.partner_id.id:
                e.do_decline()
                if e.state in state:
                    self.env['mail.activity'].sudo().search(
                        [('res_id', '=', self.id), ('user_id', '=', self.env.uid)]).action_done()

    def mark_done_overdue_activity(self):
        today = date.today() - timedelta(days=3)
        meeting = self.env.ref('advanced_conference_room.mail_act_meeting').id
        self.env['mail.activity'].sudo().search([('date_deadline', '<', today),
                                                 ('res_model', '=', 'calendar.event'),
                                                 ('activity_type_id', '=', meeting)]).action_done()
